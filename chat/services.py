import PyPDF2
import numpy as np
import faiss
import pickle
import os
import threading
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
import torch
from django.conf import settings
from .models import DocumentChunk, EmbeddingIndex
import logging
from typing import List, Dict, Generator, Optional
import asyncio
import json
from django.http import StreamingHttpResponse

logger = logging.getLogger(__name__)


class PDFProcessingService:
    def __init__(self):
        self.chunk_size = 512  # Reduced for better performance
        self.chunk_overlap = 50  # Reduced overlap

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file"""
        text_pages = []
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        text_pages.append({
                            'page': page_num + 1,
                            'text': text.strip()
                        })
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise

        return text_pages

    def create_chunks(self, text_pages):
        """Split text into chunks with improved strategy"""
        chunks = []
        chunk_index = 0

        for page_data in text_pages:
            text = page_data['text']
            page_num = page_data['page']

            # Improved chunking strategy - split by sentences first
            sentences = text.split('. ')
            current_chunk = ""
            
            for sentence in sentences:
                # If adding this sentence would exceed chunk size, save current chunk
                if len(current_chunk.split()) + len(sentence.split()) > self.chunk_size and current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'page_number': page_num,
                        'chunk_index': chunk_index
                    })
                    chunk_index += 1
                    current_chunk = sentence
                else:
                    current_chunk += ". " + sentence if current_chunk else sentence
            
            # Add the last chunk if it has content
            if current_chunk.strip():
                chunks.append({
                    'content': current_chunk.strip(),
                    'page_number': page_num,
                    'chunk_index': chunk_index
                })
                chunk_index += 1

        return chunks

    def process_document(self, document):
        """Process a PDF document and create embeddings"""
        try:
            # Extract text
            text_pages = self.extract_text_from_pdf(document.file.path)

            # Create chunks
            chunks = self.create_chunks(text_pages)
            logger.info(f"Created {len(chunks)} chunks for document: {document.title}")

            # Get embedding service instance
            embedding_service = EmbeddingService()

            # Save chunks to database first
            chunk_objects = []
            chunk_contents = []
            for chunk_data in chunks:
                chunk = DocumentChunk.objects.create(
                    document=document,
                    content=chunk_data['content'],
                    page_number=chunk_data['page_number'],
                    chunk_index=chunk_data['chunk_index']
                )
                chunk_objects.append(chunk)
                chunk_contents.append(chunk_data['content'])

            # Create embeddings in batch for better performance
            if chunk_contents:
                embeddings = embedding_service.create_embeddings_batch(chunk_contents)
                chunk_embeddings = []
                
                for chunk, embedding in zip(chunk_objects, embeddings):
                    chunk.embedding_vector = pickle.dumps(embedding)
                    chunk.save()
                    chunk_embeddings.append((chunk.id, embedding))

            # Incrementally update FAISS index instead of rebuilding
            embedding_service.add_to_faiss_index(chunk_embeddings)

            # Mark as processed
            document.processed = True
            document.processing_error = None
            document.save()

            logger.info(f"Successfully processed document: {document.title}")

        except Exception as e:
            document.processing_error = str(e)
            document.processed = False
            document.save()
            logger.error(f"Error processing document {document.title}: {str(e)}")
            raise


class EmbeddingService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
            
        # Use a better embedding model for improved accuracy
        self.model = SentenceTransformer('all-mpnet-base-v2')  # Better than all-MiniLM-L6-v2
        self.dimension = 768  # Dimension for all-mpnet-base-v2
        self.index_path = os.path.join(settings.MEDIA_ROOT, 'faiss_index.bin')
        self.mapping_path = os.path.join(settings.MEDIA_ROOT, 'chunk_mapping.pkl')
        self.initialized = True

    def create_embedding(self, text):
        """Create embedding for given text"""
        return self.model.encode([text], convert_to_tensor=False)[0]
    
    def create_embeddings_batch(self, texts):
        """Create embeddings for multiple texts at once (more efficient)"""
        return self.model.encode(texts, convert_to_tensor=False)

    def update_faiss_index(self):
        """Rebuild FAISS index with all chunks"""
        try:
            chunks = DocumentChunk.objects.filter(embedding_vector__isnull=False)

            if not chunks.exists():
                logger.warning("No chunks with embeddings found")
                return

            # Collect all embeddings
            embeddings = []
            chunk_mapping = []

            for chunk in chunks:
                if chunk.embedding_vector:
                    embedding = pickle.loads(chunk.embedding_vector)
                    embeddings.append(embedding)
                    chunk_mapping.append(chunk.id)

            if not embeddings:
                return

            # Create FAISS index
            embeddings_array = np.array(embeddings).astype('float32')  # Use float32 for better precision
            index = faiss.IndexFlatIP(self.dimension)  # Inner product for similarity
            faiss.normalize_L2(embeddings_array)  # Normalize for cosine similarity
            index.add(embeddings_array)

            # Save index and mapping
            faiss.write_index(index, self.index_path)
            with open(self.mapping_path, 'wb') as f:
                pickle.dump(chunk_mapping, f)

            # Update metadata
            EmbeddingIndex.objects.filter(is_active=True).update(is_active=False)
            EmbeddingIndex.objects.create(
                index_file=self.index_path,
                dimension=self.dimension,
                total_vectors=len(embeddings),
                is_active=True
            )

            logger.info(f"Updated FAISS index with {len(embeddings)} vectors")

        except Exception as e:
            logger.error(f"Error updating FAISS index: {str(e)}")
            raise
    
    def add_to_faiss_index(self, chunk_embeddings):
        """Add new embeddings to existing FAISS index incrementally"""
        try:
            if not chunk_embeddings:
                return
                
            # Load existing index and mapping
            if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
                index = faiss.read_index(self.index_path)
                with open(self.mapping_path, 'rb') as f:
                    chunk_mapping = pickle.load(f)
            else:
                # Create new index if it doesn't exist
                index = faiss.IndexFlatIP(self.dimension)
                chunk_mapping = []
            
            # Prepare new embeddings
            new_embeddings = []
            new_chunk_ids = []
            
            for chunk_id, embedding in chunk_embeddings:
                new_embeddings.append(embedding)
                new_chunk_ids.append(chunk_id)
            
            if new_embeddings:
                # Convert to numpy array and normalize
                embeddings_array = np.array(new_embeddings).astype('float32')
                faiss.normalize_L2(embeddings_array)
                
                # Add to index
                index.add(embeddings_array)
                
                # Update mapping
                chunk_mapping.extend(new_chunk_ids)
                
                # Save updated index and mapping
                faiss.write_index(index, self.index_path)
                with open(self.mapping_path, 'wb') as f:
                    pickle.dump(chunk_mapping, f)
                
                # Update metadata
                EmbeddingIndex.objects.filter(is_active=True).update(is_active=False)
                EmbeddingIndex.objects.create(
                    index_file=self.index_path,
                    dimension=self.dimension,
                    total_vectors=len(chunk_mapping),
                    is_active=True
                )
                
                logger.info(f"Added {len(new_embeddings)} new embeddings to FAISS index")
                
        except Exception as e:
            logger.error(f"Error adding to FAISS index: {str(e)}")
            # Fallback to full rebuild
            self.update_faiss_index()

    def search_similar_chunks(self, query_text, top_k=10, similarity_threshold=0.3):
        """Search for similar chunks using FAISS with improved accuracy"""
        try:
            if not os.path.exists(self.index_path) or not os.path.exists(self.mapping_path):
                logger.warning("FAISS index not found - no documents have been processed yet")
                return []

            # Load index and mapping
            index = faiss.read_index(self.index_path)
            with open(self.mapping_path, 'rb') as f:
                chunk_mapping = pickle.load(f)

            if not chunk_mapping:
                logger.warning("No chunks in mapping - index may be empty")
                return []

            # Create query embedding
            query_embedding = self.create_embedding(query_text)
            query_vector = np.array([query_embedding]).astype('float32')
            faiss.normalize_L2(query_vector)

            # Search with more results to filter by threshold
            search_k = min(top_k * 3, len(chunk_mapping))  # Get more results to filter
            scores, indices = index.search(query_vector, search_k)

            # Get corresponding chunks with better filtering
            similar_chunks = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(chunk_mapping) and score > similarity_threshold:
                    chunk_id = chunk_mapping[idx]
                    try:
                        chunk = DocumentChunk.objects.get(id=chunk_id)
                        similar_chunks.append({
                            'chunk': chunk,
                            'similarity': float(score)
                        })
                    except DocumentChunk.DoesNotExist:
                        logger.warning(f"Chunk {chunk_id} not found in database")
                        continue
                
                # Stop if we have enough high-quality results
                if len(similar_chunks) >= top_k:
                    break

            # Sort by similarity score (descending)
            similar_chunks.sort(key=lambda x: x['similarity'], reverse=True)
            logger.info(f"Found {len(similar_chunks)} similar chunks for query")
            return similar_chunks[:top_k]

        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}", exc_info=True)
            return []


class ChatService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
            
        self.model = None
        self.tokenizer = None
        
        # Check CUDA availability with proper error handling
        try:
            if torch.cuda.is_available():
                # Test CUDA functionality
                test_tensor = torch.tensor([1.0]).cuda()
                self.device = "cuda"
                logger.info(f"CUDA is working properly. Device: {torch.cuda.get_device_name()}")
            else:
                self.device = "cpu"
                logger.info("CUDA not available, using CPU")
        except Exception as e:
            logger.warning(f"CUDA initialization failed: {e}. Falling back to CPU.")
            self.device = "cpu"
        
        self.embedding_service = EmbeddingService()
        self.initialized = True
        logger.info(f"ChatService initialized on device: {self.device}")

    def load_model(self):
        try:
            if self.model is None:
                model_path = os.path.join(settings.BASE_DIR, "models/phi-2")
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)

                # Configure padding token
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                    self.tokenizer.padding_side = 'left'  # Better for casual language models

                # Optimize device settings based on actual device
                if self.device == "cuda":
                    try:
                        # Test CUDA again before using it
                        test_tensor = torch.tensor([1.0]).cuda()
                        torch_dtype = torch.float16  # Use float16 for better GPU performance
                        device_map = "auto"
                        
                        # Enable GPU memory optimization
                        torch.backends.cudnn.benchmark = True
                        torch.backends.cuda.matmul.allow_tf32 = True
                        torch.backends.cudnn.allow_tf32 = True
                        
                        # Clear GPU cache
                        torch.cuda.empty_cache()
                        
                        logger.info(f"Using GPU: {torch.cuda.get_device_name()}")
                        logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
                        logger.info(f"Available GPU Memory: {torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated() / 1024**3:.1f} GB")
                    except Exception as e:
                        logger.warning(f"GPU failed during model loading: {e}. Falling back to CPU.")
                        self.device = "cpu"
                        torch_dtype = torch.float32
                        device_map = None
                else:
                    torch_dtype = torch.float32
                    device_map = None
                    logger.info("Using CPU for model loading")

                # Load model with optimized settings
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch_dtype,
                    trust_remote_code=True,
                    device_map=device_map,
                    low_cpu_mem_usage=True,
                    use_cache=True,  # Enable KV cache for faster generation
                )
                self.model.config.pad_token_id = self.tokenizer.pad_token_id
                self.model.eval()
                
                # Move to device if not using device_map
                if device_map is None:
                    self.model = self.model.to(self.device)
                
                logger.info(f"Successfully loaded Phi-2 model from {model_path} on {self.device}")
        except Exception as e:
            logger.error(f"Error loading Phi-2 model: {str(e)}")
            raise
    
    def clear_gpu_cache(self):
        """Clear GPU cache to free memory"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # def generate_response(self, messages):
    #     try:
    #         if self.model is None:
    #             self.load_model()
    #
    #         # Format conversation history
    #         conversation = ""
    #         for msg in messages:
    #             role = "Human: " if msg.message_type == 'user' else "Assistant: "
    #             conversation += f"{role}{msg.content}\n"
    #
    #         conversation += "Assistant: "
    #
    #         # Create input tokens with proper attention mask
    #         inputs = self.tokenizer(
    #             conversation,
    #             return_tensors="pt",
    #             truncation=True,
    #             max_length=2048,
    #             padding=True,
    #             add_special_tokens=True,
    #             return_attention_mask=True
    #         )
    #
    #         # Generate response with attention mask
    #         outputs = self.model.generate(
    #             input_ids=inputs["input_ids"],
    #             attention_mask=inputs["attention_mask"],
    #             max_length=4096,
    #             num_return_sequences=1,
    #             temperature=0.7,
    #             do_sample=True,
    #             pad_token_id=self.tokenizer.pad_token_id,
    #             eos_token_id=self.tokenizer.eos_token_id,
    #             repetition_penalty=1.2,
    #             no_repeat_ngram_size=3,
    #             use_cache=True
    #         )
    #
    #         # Decode the response
    #         response = self.tokenizer.decode(
    #             outputs[0][inputs["input_ids"].shape[1]:],
    #             skip_special_tokens=True,
    #             clean_up_tokenization_spaces=True
    #         )
    #
    #         # Clean up the response
    #         response = response.strip()
    #         if not response:
    #             response = "I apologize, but I couldn't generate a meaningful response. Please try rephrasing your question."
    #
    #         return response
    #
    #     except Exception as e:
    #         logger.error(f"Error generating response: {str(e)}")
    #         raise

    def get_relevant_context(self, query: str, top_k: int = 3) -> str:
        """Retrieve relevant context from documents using RAG"""
        try:
            similar_chunks = self.embedding_service.search_similar_chunks(query, top_k=top_k)
            
            if not similar_chunks:
                logger.info("No relevant chunks found, will generate response without context")
                return ""
            
            context_parts = []
            for chunk_data in similar_chunks:
                chunk = chunk_data['chunk']
                context_parts.append(f"Document: {chunk.document.title}\nContent: {chunk.content}")
            
            logger.info(f"Found {len(similar_chunks)} relevant chunks for context")
            return "\n\n".join(context_parts)
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return ""

    def _format_context_from_chunks(self, similar_chunks) -> str:
        """Format a context string from provided similar chunks."""
        try:
            if not similar_chunks:
                return ""
            context_parts = []
            for chunk_data in similar_chunks:
                chunk = chunk_data['chunk']
                context_parts.append(
                    f"Document: {chunk.document.title}\nPage: {chunk.page_number}\nContent: {chunk.content}"
                )
            return "\n\n".join(context_parts)
        except Exception as e:
            logger.warning(f"Error formatting context from chunks: {e}")
            return ""
    
    def generate_response(self, messages, similar_chunks=None):
        """Generate response with RAG (Retrieval-Augmented Generation) - optimized for speed"""
        try:
            if self.model is None:
                self.load_model()
            
            user_prompt = messages[-1].content
            
            # Get relevant context from documents (prefer provided chunks)
            context = self._format_context_from_chunks(similar_chunks) if similar_chunks else self.get_relevant_context(user_prompt)
            
            # Require KB context; don't generate generic answers
            if not context:
                return "I could not find information in the knowledge base about that. Please rephrase or upload relevant documents."
            formatted_prompt = f"""### Context (knowledge base excerpts):
{context}

### Task:
You are a public health expert responding to a question using ONLY the information provided above in the Context section.

STRICT RULES:
- Do NOT use any outside or prior knowledge.
- Do NOT guess or generalize.
- Do NOT paraphrase based on your own understanding.
- You MAY treat synonyms or clearly equivalent terms in the user question as matching those in the Context.
- If the answer is not clearly stated in the Context or cannot be inferred through synonymous phrasing, respond exactly: "I could not find information in the knowledge base about that."

INSTRUCTIONS FOR YOUR RESPONSE:
- Begin with a simple, direct explanation in full sentences.
- Use details and examples from the Context where possible.
- If helpful, synthesize across multiple excerpts in the Context.
- End your answer with 2–4 concise bullet point takeaways that summarize the key ideas.

Maintain a factual, professional tone. Do not mention or reference the Context section in your answer.

User question:
{user_prompt}

### Response:
"""

#             formatted_prompt = f"""### Context (knowledge base excerpts):
# {context}

# ### Task:
# You are a public health expert responding to a question using ONLY the information provided above in the Context section.

# STRICT RULES:
# - Do NOT use any outside or prior knowledge.
# - Do NOT guess or generalize.
# - Do NOT paraphrase based on your own understanding.
# - If the answer is not clearly stated in the Context, respond exactly: "I could not find information in the knowledge base about that."

# INSTRUCTIONS FOR YOUR RESPONSE:
# - Begin with a simple, direct explanation in full sentences.
# - Use details and examples from the Context where possible.
# - If helpful, synthesize across multiple excerpts in the Context.
# - End your answer with 2–4 concise bullet point takeaways that summarize the key ideas.

# Maintain a factual, professional tone. Do not mention or reference the Context section in your answer.

# User question:
# {user_prompt}

# ### Response:
# """




            # Build prompt with strict instruction to use only the context
#             formatted_prompt = f"""### Context (knowledge base excerpts):
# {context}

# ### Instruction:
# Using ONLY the information in the Context, write a clear, well-structured answer in full paragraphs. Synthesize across documents when helpful. Do not mention that you used a context. If the answer is not present in the Context, reply exactly: "I could not find information in the knowledge base about that."

# Guidelines:
# - Aim for a concise but complete explanation (6-12 sentences)
# - Use a neutral, informative tone
# - Avoid bullet lists unless necessary

# User question:
# {user_prompt}

# ### Response:
# """

            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)

            # Optimized generation settings for completeness and speed
            with torch.no_grad():
                generation_kwargs = {
                    **inputs,
                    "max_new_tokens": 512,  # Allow longer, more complete answers
                    "do_sample": False,
                    "top_p": 0.8,
                    "temperature": 0.0,
                    "pad_token_id": self.tokenizer.pad_token_id,
                    "eos_token_id": self.tokenizer.eos_token_id,
                    "repetition_penalty": 1.1,
                    "no_repeat_ngram_size": 3,
                    "use_cache": True,  # Enable KV cache
                    "num_beams": 1,     # Faster than beam search
                    "early_stopping": True,
                }
                
                # Add CPU-specific optimizations
                if self.device == "cpu":
                    generation_kwargs["max_new_tokens"] = 256  # Balanced for CPU
                    generation_kwargs["do_sample"] = False  # Greedy decoding is faster on CPU
                
                output = self.model.generate(**generation_kwargs)

            response = self.tokenizer.decode(output[0], skip_special_tokens=True)
            response = response.split("### Response:")[-1].strip()

            if not response:
                return "I'm here to help! How can I assist you today?"

            # Clear GPU cache after generation
            self.clear_gpu_cache()
            return response

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'm sorry, there was an error processing your request."
    
    def generate_response_stream(self, messages, similar_chunks=None) -> Generator[str, None, None]:
        """Generate streaming response with RAG - fast real-time streaming like ChatGPT"""
        try:
            if self.model is None:
                self.load_model()
            
            user_prompt = messages[-1].content
            
            # Get relevant context from documents (prefer provided chunks)
            context = self._format_context_from_chunks(similar_chunks) if similar_chunks else self.get_relevant_context(user_prompt)
            
            # Require KB context; don't generate generic answers
            if not context:
                yield "I could not find information in the knowledge base about that. Please rephrase or upload relevant documents."
                return
            formatted_prompt = f"""### Context (knowledge base excerpts):
{context}

### Task:
You are a public health expert responding to a question using ONLY the information provided above in the Context section.

STRICT RULES:
- Do NOT use any outside or prior knowledge.
- Do NOT guess or generalize.
- Do NOT paraphrase based on your own understanding.
- You MAY treat synonyms or clearly equivalent terms in the user question as matching those in the Context.
- If the answer is not clearly stated in the Context or cannot be inferred through synonymous phrasing, respond exactly: "I could not find information in the knowledge base about that."

INSTRUCTIONS FOR YOUR RESPONSE:
- Begin with a simple, direct explanation in full sentences.
- Use details and examples from the Context where possible.
- If helpful, synthesize across multiple excerpts in the Context.
- End your answer with 2–4 concise bullet point takeaways that summarize the key ideas.

Maintain a factual, professional tone. Do not mention or reference the Context section in your answer.

User question:
{user_prompt}

### Response:
"""

#             formatted_prompt = f"""### Context (knowledge base excerpts):
# {context}

# ### Task:
# You are a public health expert responding to a question using ONLY the information provided above in the Context section.

# STRICT RULES:
# - Do NOT use any outside or prior knowledge.
# - Do NOT guess or generalize.
# - Do NOT paraphrase based on your own understanding.
# - If the answer is not clearly stated in the Context, respond exactly: "I could not find information in the knowledge base about that."


# INSTRUCTIONS FOR YOUR RESPONSE:
# - Begin with a simple, direct explanation in full sentences.
# - Use details and examples from the Context where possible.
# - If helpful, synthesize across multiple excerpts in the Context.
# - End your answer with 2–4 concise bullet point takeaways that summarize the key ideas.

# Maintain a factual, professional tone. Do not mention or reference the Context section in your answer.

# User question:
# {user_prompt}

# ### Response:
# """




            # Build prompt with strict instruction to use only the context
#             formatted_prompt = f"""### Context (knowledge base excerpts):
# {context}

# ### Instruction:
# Using ONLY the information in the Context, write a clear, well-structured answer in full paragraphs. Synthesize across documents when helpful. Do not mention that you used a context. If the answer is not present in the Context, reply exactly: "I could not find information in the knowledge base about that."

# Guidelines:
# - Aim for a concise but complete explanation (6-12 sentences)
# - Use a neutral, informative tone
# - Avoid bullet lists unless necessary

# User question:
# {user_prompt}

# ### Response:
# """

            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)

            # Use optimized generation settings for fast streaming
            with torch.no_grad():
                # Generate the entire response first (much faster)
                generation_kwargs = {
                    **inputs,
                    "max_new_tokens": 512,  # Allow longer answers
                    "do_sample": False,
                    "top_p": 0.8,
                    "temperature": 0.0,
                    "pad_token_id": self.tokenizer.pad_token_id,
                    "eos_token_id": self.tokenizer.eos_token_id,
                    "repetition_penalty": 1.1,
                    "no_repeat_ngram_size": 3,
                    "use_cache": True,
                    "num_beams": 1,
                    "early_stopping": True,
                }
                
                # Add CPU-specific optimizations
                if self.device == "cpu":
                    generation_kwargs["max_new_tokens"] = 256
                    generation_kwargs["do_sample"] = False  # Greedy decoding is faster on CPU
                
                outputs = self.model.generate(**generation_kwargs)
                
                # Decode the full response
                full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Extract only the response part (after "### Response:")
                if "### Response:" in full_response:
                    response_text = full_response.split("### Response:")[-1].strip()
                else:
                    response_text = full_response.strip()
                
                if not response_text:
                    response_text = "I'm here to help! How can I assist you today?"
                
                # Stream the response in small chunks for fast, smooth effect
                import time
                chunk_size = 3  # Stream 3 characters at a time
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i + chunk_size]
                    yield chunk
                    # Very small delay for smooth streaming (like ChatGPT)
                    time.sleep(0.01)  # 10ms delay - fast but visible
                
                # Clear GPU cache after generation
                self.clear_gpu_cache()

        except Exception as e:
            logger.error(f"Error generating streaming response: {str(e)}", exc_info=True)
            yield "I'm sorry, there was an error processing your request."

    # def generate_response(self, messages):
    #     try:
    #         # Format prompt
    #         user_prompt = messages[-1].content  # Assuming the last message is the user's
    #         formatted_prompt = f"### Instruction:\n{user_prompt}\n\n### Response:\n"
    #
    #         inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)
    #         from transformers import TextStreamer
    #
    #         # Assuming you've set up the tokenizer and model properly.
    #         streamer = TextStreamer(self.tokenizer)
    #
    #         output = self.model.generate(
    #             **inputs,
    #             max_new_tokens=256,
    #             do_sample=True,
    #             top_p=0.95,
    #             temperature=0.7,
    #             pad_token_id=self.tokenizer.pad_token_id,
    #             eos_token_id=self.tokenizer.eos_token_id,
    #             streamer=streamer
    #         )
    #
    #         response = self.tokenizer.decode(output[0], skip_special_tokens=True)
    #         print("🧠 Model output:", response)
    #         return response.split("### Response:")[-1].strip()
    #
    #     except Exception as e:
    #         print("❌ Error generating response:", e)
    #         return "I apologize, but I couldn't generate a meaningful response. Please try rephrasing your question."

