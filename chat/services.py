# import PyPDF2
# import numpy as np
# import faiss
# import pickle
# import os
# import threading
# from sentence_transformers import SentenceTransformer
# import ollama
# from django.conf import settings
# from .models import DocumentChunk, EmbeddingIndex
# import logging
# from typing import List, Dict, Generator, Optional
# import asyncio
# import json
# from django.http import StreamingHttpResponse
# import time

# logger = logging.getLogger(__name__)


# class PDFProcessingService:
#     def __init__(self):
#         self.chunk_size = 512  # Reduced for better performance
#         self.chunk_overlap = 50  # Reduced overlap

#     def extract_text_from_pdf(self, pdf_path):
#         """Extract text from PDF file"""
#         text_pages = []
#         try:
#             with open(pdf_path, 'rb') as file:
#                 pdf_reader = PyPDF2.PdfReader(file)
#                 for page_num, page in enumerate(pdf_reader.pages):
#                     text = page.extract_text()
#                     if text.strip():
#                         text_pages.append({
#                             'page': page_num + 1,
#                             'text': text.strip()
#                         })
#         except Exception as e:
#             logger.error(f"Error extracting text from PDF: {str(e)}")
#             raise

#         return text_pages

#     def create_chunks(self, text_pages):
#         """Split text into chunks with improved strategy"""
#         chunks = []
#         chunk_index = 0

#         for page_data in text_pages:
#             text = page_data['text']
#             page_num = page_data['page']

#             # Improved chunking strategy - split by sentences first
#             sentences = text.split('. ')
#             current_chunk = ""
            
#             for sentence in sentences:
#                 # If adding this sentence would exceed chunk size, save current chunk
#                 if len(current_chunk.split()) + len(sentence.split()) > self.chunk_size and current_chunk:
#                     chunks.append({
#                         'content': current_chunk.strip(),
#                         'page_number': page_num,
#                         'chunk_index': chunk_index
#                     })
#                     chunk_index += 1
#                     current_chunk = sentence
#                 else:
#                     current_chunk += ". " + sentence if current_chunk else sentence
            
#             # Add the last chunk if it has content
#             if current_chunk.strip():
#                 chunks.append({
#                     'content': current_chunk.strip(),
#                     'page_number': page_num,
#                     'chunk_index': chunk_index
#                 })
#                 chunk_index += 1

#         return chunks

#     def process_document(self, document):
#         """Process a PDF document and create embeddings"""
#         try:
#             # Extract text
#             text_pages = self.extract_text_from_pdf(document.file.path)

#             # Create chunks
#             chunks = self.create_chunks(text_pages)
#             logger.info(f"Created {len(chunks)} chunks for document: {document.title}")

#             # Get embedding service instance
#             embedding_service = EmbeddingService()

#             # Save chunks to database first
#             chunk_objects = []
#             chunk_contents = []
#             for chunk_data in chunks:
#                 chunk = DocumentChunk.objects.create(
#                     document=document,
#                     content=chunk_data['content'],
#                     page_number=chunk_data['page_number'],
#                     chunk_index=chunk_data['chunk_index']
#                 )
#                 chunk_objects.append(chunk)
#                 chunk_contents.append(chunk_data['content'])

#             # Create embeddings in batch for better performance
#             if chunk_contents:
#                 embeddings = embedding_service.create_embeddings_batch(chunk_contents)
#                 chunk_embeddings = []
                
#                 for chunk, embedding in zip(chunk_objects, embeddings):
#                     chunk.embedding_vector = pickle.dumps(embedding)
#                     chunk.save()
#                     chunk_embeddings.append((chunk.id, embedding))

#             # Incrementally update FAISS index instead of rebuilding
#             embedding_service.add_to_faiss_index(chunk_embeddings)

#             # Mark as processed
#             document.processed = True
#             document.processing_error = None
#             document.save()

#             logger.info(f"Successfully processed document: {document.title}")

#         except Exception as e:
#             document.processing_error = str(e)
#             document.processed = False
#             document.save()
#             logger.error(f"Error processing document {document.title}: {str(e)}")
#             raise


# class EmbeddingService:
#     _instance = None
#     _lock = threading.Lock()
    
#     def __new__(cls):
#         if cls._instance is None:
#             with cls._lock:
#                 if cls._instance is None:
#                     cls._instance = super().__new__(cls)
#         return cls._instance
    
#     def __init__(self):
#         if hasattr(self, 'initialized'):
#             return
            
#         # Use the best embedding model for improved accuracy and retrieval
#         # BAAI/bge-large-en-v1.5 is currently one of the best English embedding models
#         self.model = SentenceTransformer('BAAI/bge-large-en-v1.5')
#         self.dimension = 1024  # Dimension for BAAI/bge-large-en-v1.5
#         self.index_path = os.path.join(settings.MEDIA_ROOT, 'faiss_index.bin')
#         self.mapping_path = os.path.join(settings.MEDIA_ROOT, 'chunk_mapping.pkl')
#         self.initialized = True
#         logger.info(f"Initialized EmbeddingService with BAAI/bge-large-en-v1.5 (dim={self.dimension})")

#     def create_embedding(self, text):
#         """Create embedding for given text with query prefix for BGE model"""
#         # BGE models work better with instruction prefix for queries
#         prefixed_text = f"Represent this sentence for searching relevant passages: {text}"
#         return self.model.encode([prefixed_text], convert_to_tensor=False)[0]
    
#     def create_embeddings_batch(self, texts):
#         """Create embeddings for multiple texts at once (more efficient)"""
#         return self.model.encode(texts, convert_to_tensor=False)

#     def update_faiss_index(self):
#         """Rebuild FAISS index with all chunks"""
#         try:
#             chunks = DocumentChunk.objects.filter(embedding_vector__isnull=False)

#             if not chunks.exists():
#                 logger.warning("No chunks with embeddings found")
#                 return

#             # Collect all embeddings
#             embeddings = []
#             chunk_mapping = []

#             for chunk in chunks:
#                 if chunk.embedding_vector:
#                     embedding = pickle.loads(chunk.embedding_vector)
#                     embeddings.append(embedding)
#                     chunk_mapping.append(chunk.id)

#             if not embeddings:
#                 return

#             # Create FAISS index
#             embeddings_array = np.array(embeddings).astype('float32')  # Use float32 for better precision
#             index = faiss.IndexFlatIP(self.dimension)  # Inner product for similarity
#             faiss.normalize_L2(embeddings_array)  # Normalize for cosine similarity
#             index.add(embeddings_array)

#             # Save index and mapping
#             faiss.write_index(index, self.index_path)
#             with open(self.mapping_path, 'wb') as f:
#                 pickle.dump(chunk_mapping, f)

#             # Update metadata
#             EmbeddingIndex.objects.filter(is_active=True).update(is_active=False)
#             EmbeddingIndex.objects.create(
#                 index_file=self.index_path,
#                 dimension=self.dimension,
#                 total_vectors=len(embeddings),
#                 is_active=True
#             )

#             logger.info(f"Updated FAISS index with {len(embeddings)} vectors")

#         except Exception as e:
#             logger.error(f"Error updating FAISS index: {str(e)}")
#             raise
    
#     def add_to_faiss_index(self, chunk_embeddings):
#         """Add new embeddings to existing FAISS index incrementally"""
#         try:
#             if not chunk_embeddings:
#                 return
                
#             # Load existing index and mapping
#             if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
#                 index = faiss.read_index(self.index_path)
#                 with open(self.mapping_path, 'rb') as f:
#                     chunk_mapping = pickle.load(f)
#             else:
#                 # Create new index if it doesn't exist
#                 index = faiss.IndexFlatIP(self.dimension)
#                 chunk_mapping = []
            
#             # Prepare new embeddings
#             new_embeddings = []
#             new_chunk_ids = []
            
#             for chunk_id, embedding in chunk_embeddings:
#                 new_embeddings.append(embedding)
#                 new_chunk_ids.append(chunk_id)
            
#             if new_embeddings:
#                 # Convert to numpy array and normalize
#                 embeddings_array = np.array(new_embeddings).astype('float32')
#                 faiss.normalize_L2(embeddings_array)
                
#                 # Add to index
#                 index.add(embeddings_array)
                
#                 # Update mapping
#                 chunk_mapping.extend(new_chunk_ids)
                
#                 # Save updated index and mapping
#                 faiss.write_index(index, self.index_path)
#                 with open(self.mapping_path, 'wb') as f:
#                     pickle.dump(chunk_mapping, f)
                
#                 # Update metadata
#                 EmbeddingIndex.objects.filter(is_active=True).update(is_active=False)
#                 EmbeddingIndex.objects.create(
#                     index_file=self.index_path,
#                     dimension=self.dimension,
#                     total_vectors=len(chunk_mapping),
#                     is_active=True
#                 )
                
#                 logger.info(f"Added {len(new_embeddings)} new embeddings to FAISS index")
                
#         except Exception as e:
#             logger.error(f"Error adding to FAISS index: {str(e)}")
#             # Fallback to full rebuild
#             self.update_faiss_index()

#     def search_similar_chunks(self, query_text, top_k=40, similarity_threshold=0.4):
#         """Search for similar chunks using FAISS with improved accuracy"""
#         try:
#             if not os.path.exists(self.index_path) or not os.path.exists(self.mapping_path):
#                 logger.warning("FAISS index not found - no documents have been processed yet")
#                 return []

#             # Load index and mapping
#             index = faiss.read_index(self.index_path)
#             with open(self.mapping_path, 'rb') as f:
#                 chunk_mapping = pickle.load(f)

#             if not chunk_mapping:
#                 logger.warning("No chunks in mapping - index may be empty")
#                 return []

#             # Create query embedding
#             query_embedding = self.create_embedding(query_text)
#             query_vector = np.array([query_embedding]).astype('float32')
#             faiss.normalize_L2(query_vector)

#             # Search with more results to filter by threshold
#             search_k = min(top_k * 3, len(chunk_mapping))  # Get more results to filter
#             scores, indices = index.search(query_vector, search_k)

#             # Get corresponding chunks with better filtering
#             similar_chunks = []
#             for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
#                 if idx < len(chunk_mapping) and score > similarity_threshold:
#                     chunk_id = chunk_mapping[idx]
#                     try:
#                         chunk = DocumentChunk.objects.get(id=chunk_id)
#                         similar_chunks.append({
#                             'chunk': chunk,
#                             'similarity': float(score)
#                         })
#                     except DocumentChunk.DoesNotExist:
#                         logger.warning(f"Chunk {chunk_id} not found in database")
#                         continue
                
#                 # Stop if we have enough high-quality results
#                 if len(similar_chunks) >= top_k:
#                     break

#             # Sort by similarity score (descending)
#             similar_chunks.sort(key=lambda x: x['similarity'], reverse=True)
#             logger.info(f"Found {len(similar_chunks)} similar chunks for query")
#             return similar_chunks[:top_k]

#         except Exception as e:
#             logger.error(f"Error searching similar chunks: {str(e)}", exc_info=True)
#             return []


# class ChatService:
#     _instance = None
#     _lock = threading.Lock()
    
#     def __new__(cls):
#         if cls._instance is None:
#             with cls._lock:
#                 if cls._instance is None:
#                     cls._instance = super().__new__(cls)
#         return cls._instance
    
#     def __init__(self):
#         if hasattr(self, 'initialized'):
#             return
            
#         # Use Ollama for optimized model management
#         self.ollama_client = ollama.Client()
#         self.model_name = "phi4-mini:latest"
        
#         # Test Ollama connection
#         try:
#             models = self.ollama_client.list()
#             available_models = [m.model for m in models['models']]
#             if self.model_name in available_models:
#                 logger.info(f"✓ Ollama connected. Using {self.model_name}")
#                 self.ollama_available = True
#             else:
#                 logger.error(f"Model {self.model_name} not found in Ollama. Available: {available_models}")
#                 self.ollama_available = False
#         except Exception as e:
#             logger.error(f"Failed to connect to Ollama: {e}")
#             self.ollama_available = False
        
#         self.embedding_service = EmbeddingService()
#         self.initialized = True
#         logger.info("ChatService initialized with Ollama backend")

#     def load_model(self):
#         """Load model through Ollama - no manual loading needed"""
#         if not self.ollama_available:
#             raise Exception("Ollama not available. Please ensure Ollama is running and phi3:mini is installed.")
        
#         # Test the model
#         try:
#             response = self.ollama_client.generate(
#                 model=self.model_name,
#                 prompt="Test",
#                 stream=False
#             )
#             logger.info(f"✓ {self.model_name} model ready via Ollama")
#         except Exception as e:
#             logger.error(f"Error testing Ollama model: {str(e)}")
#             raise
    
#     def clear_gpu_cache(self):
#         """Clear GPU cache to free memory"""
#         if torch.cuda.is_available():
#             torch.cuda.empty_cache()

#     # def generate_response(self, messages):
#     #     try:
#     #         if self.model is None:
#     #             self.load_model()
#     #
#     #         # Format conversation history
#     #         conversation = ""
#     #         for msg in messages:
#     #             role = "Human: " if msg.message_type == 'user' else "Assistant: "
#     #             conversation += f"{role}{msg.content}\n"
#     #
#     #         conversation += "Assistant: "
#     #
#     #         # Create input tokens with proper attention mask
#     #         inputs = self.tokenizer(
#     #             conversation,
#     #             return_tensors="pt",
#     #             truncation=True,
#     #             max_length=2048,
#     #             padding=True,
#     #             add_special_tokens=True,
#     #             return_attention_mask=True
#     #         )
#     #
#     #         # Generate response with attention mask
#     #         outputs = self.model.generate(
#     #             input_ids=inputs["input_ids"],
#     #             attention_mask=inputs["attention_mask"],
#     #             max_length=4096,
#     #             num_return_sequences=1,
#     #             temperature=0.7,
#     #             do_sample=True,
#     #             pad_token_id=self.tokenizer.pad_token_id,
#     #             eos_token_id=self.tokenizer.eos_token_id,
#     #             repetition_penalty=1.2,
#     #             no_repeat_ngram_size=3,
#     #             use_cache=True
#     #         )
#     #
#     #         # Decode the response
#     #         response = self.tokenizer.decode(
#     #             outputs[0][inputs["input_ids"].shape[1]:],
#     #             skip_special_tokens=True,
#     #             clean_up_tokenization_spaces=True
#     #         )
#     #
#     #         # Clean up the response
#     #         response = response.strip()
#     #         if not response:
#     #             response = "I apologize, but I couldn't generate a meaningful response. Please try rephrasing your question."
#     #
#     #         return response
#     #
#     #     except Exception as e:
#     #         logger.error(f"Error generating response: {str(e)}")
#     #         raise

#     def get_relevant_context(self, query: str, top_k: int = 5) -> str:
#         """Retrieve relevant context from documents using RAG"""
#         try:
#             similar_chunks = self.embedding_service.search_similar_chunks(query, top_k=top_k)
            
#             if not similar_chunks:
#                 logger.info("No relevant chunks found, will generate response without context")
#                 return ""
            
#             context_parts = []
#             for chunk_data in similar_chunks:
#                 chunk = chunk_data['chunk']
#                 context_parts.append(f"Document: {chunk.document.title}\nContent: {chunk.content}")
            
#             logger.info(f"Found {len(similar_chunks)} relevant chunks for context")
#             return "\n\n".join(context_parts)
#         except Exception as e:
#             logger.error(f"Error retrieving context: {str(e)}")
#             return ""

#     def _format_context_from_chunks(self, similar_chunks) -> str:
#         """Format a context string from provided similar chunks."""
#         try:
#             if not similar_chunks:
#                 return ""
#             context_parts = []
#             for chunk_data in similar_chunks:
#                 chunk = chunk_data['chunk']
#                 context_parts.append(
#                     f"Document: {chunk.document.title}\nContent: {chunk.content}"
#                 )
#             return "\n\n".join(context_parts)
#         except Exception as e:
#             logger.warning(f"Error formatting context from chunks: {e}")
#             return ""
    
#     def generate_response(self, messages, similar_chunks=None):
#         """Generate response with RAG (Retrieval-Augmented Generation) - optimized for speed"""
#         try:
#             if not self.ollama_available:
#                 self.load_model()
            
#             user_prompt = messages[-1].content
            
#             # Get relevant context from documents (prefer provided chunks)
#             context = self._format_context_from_chunks(similar_chunks) if similar_chunks else self.get_relevant_context(user_prompt)
            
#             # Require KB context; don't generate generic answers
#             if not context:
#                 return "I could not find information in the knowledge base about that. Please rephrase or upload relevant documents."
            
#             # Create optimized prompt for Ollama
#             # Replace your system_prompt in both generate_response() and generate_response_stream() with this:

#             # Replace your system_prompt in both generate_response() and generate_response_stream() with this:

#             # Use this exact system prompt in your services.py file:

#             system_prompt = """You are a professional knowledge assistant. Format responses clearly with headings, paragraphs, and occasional bullet lists.

# FORMATTING REQUIREMENTS:

# 1. HEADINGS - Use **bold** for section titles:
#    - Format: **Section Title**
#    - Must be on its own line
#    - Add ONE blank line before it
#    - Add ONE blank line after it
#    - Never use ### or #

# 2. PARAGRAPHS - Use for explanations:
#    - Write 2-4 complete sentences per paragraph
#    - Add ONE blank line between paragraphs
#    - Do NOT start paragraphs with bullets

# 3. BULLET LISTS - Use only for listing items:
#    - Add ONE blank line before the list
#    - Format each bullet: - Item text
#    - Add ONE blank line after the list
#    - Use bullets for 3+ related items only

# EXAMPLE OF CORRECT FORMAT:

# **Consultation**

# Consultation involves seeking advice from community members on specific issues. The Health Department shares information and seeks feedback but retains final decision-making authority.

# Key aspects include:

# - Information sharing without full incorporation of input
# - Feedback is considered but may not influence decisions
# - Health Department retains ultimate authority

# **Collaboration**

# Collaboration involves working together as equal partners. Decisions are made through consensus between all parties.

# WHAT NOT TO DO:
# - Do NOT use bullets for every sentence
# - Do NOT put bullets before headings
# - Do NOT write one-sentence paragraphs followed by bullets
# - Do NOT use ---, ###, or other special characters

# CONTENT RULES:
# - Answer using ONLY the provided context
# - If not in context: "I could not find information in the knowledge base about that."
# - Be clear, professional, and well-structured"""

#             user_message = f"""
# CONTEXT from Knowledge Base:

# {context}

# USER QUESTION:

# {user_prompt}

# Please provide a comprehensive, well-formatted answer using the context above. Structure your response with:
# - Clear headings for main concepts
# - Explanatory paragraphs
# - Bullet points for key details
# - Proper spacing and line breaks

# Remember: Do NOT use ---, ###, or any special markdown characters in your response.
# """




# #             formatted_prompt = f"""### Context (knowledge base excerpts):
# # {context}

# # ### Task:
# # You are a public health expert responding to a question using ONLY the information provided above in the Context section.

# # STRICT RULES:
# # - Do NOT use any outside or prior knowledge.
# # - Do NOT guess or generalize.
# # - Do NOT paraphrase based on your own understanding.
# # - If the answer is not clearly stated in the Context, respond exactly: "I could not find information in the knowledge base about that."

# # INSTRUCTIONS FOR YOUR RESPONSE:
# # - Begin with a simple, direct explanation in full sentences.
# # - Use details and examples from the Context where possible.
# # - If helpful, synthesize across multiple excerpts in the Context.
# # - End your answer with 2–4 concise bullet point takeaways that summarize the key ideas.

# # Maintain a factual, professional tone. Do not mention or reference the Context section in your answer.

# # User question:
# # {user_prompt}

# # ### Response:
# # """




#             # Build prompt with strict instruction to use only the context
# #             formatted_prompt = f"""### Context (knowledge base excerpts):
# # {context}

# # ### Instruction:
# # Using ONLY the information in the Context, write a clear, well-structured answer in full paragraphs. Synthesize across documents when helpful. Do not mention that you used a context. If the answer is not present in the Context, reply exactly: "I could not find information in the knowledge base about that."

# # Guidelines:
# # - Aim for a concise but complete explanation (6-12 sentences)
# # - Use a neutral, informative tone
# # - Avoid bullet lists unless necessary

# # User question:
# # {user_prompt}

# # ### Response:
# # """

#             # Generate response using Ollama
#             response = self.ollama_client.chat(
#                 model=self.model_name,
#                 messages=[
#                     {'role': 'system', 'content': system_prompt},
#                     {'role': 'user', 'content': user_message}
#                 ],
#                 stream=False,
#                 options={
#                     'temperature': 0.3,
#                     'top_p': 0.9,
#                     'repeat_penalty': 1.2,
#                     'num_ctx': 4096,
#                 }
#             )
            
#             generated_text = response['message']['content'].strip()
            
#             if not generated_text:
#                 return "I'm here to help! How can I assist you today?"
                
#             return generated_text

#         except Exception as e:
#             logger.error(f"Error generating response with Ollama: {str(e)}")
#             return "I'm sorry, there was an error processing your request."
    
#     def generate_response_stream(self, messages, similar_chunks=None) -> Generator[str, None, None]:
#         """Generate streaming response with RAG using Ollama backend"""
#         try:
#             if not self.ollama_available:
#                 self.load_model()
            
#             user_prompt = messages[-1].content
            
#             # Get relevant context from documents (prefer provided chunks)
#             context = self._format_context_from_chunks(similar_chunks) if similar_chunks else self.get_relevant_context(user_prompt)
            
#             # Require KB context; don't generate generic answers
#             if not context:
#                 yield "I could not find information in the knowledge base about that. Please rephrase or upload relevant documents."
#                 return
            
#             # Create optimized prompt for Ollama
#             # Replace your system_prompt in both generate_response() and generate_response_stream() with this:

#             # Replace your system_prompt in both generate_response() and generate_response_stream() with this:

#             # Use this exact system prompt in your services.py file:

#             system_prompt = """You are a professional knowledge assistant. Format responses clearly with headings, paragraphs, and occasional bullet lists.

# FORMATTING REQUIREMENTS:

# 1. HEADINGS - Use **bold** for section titles:
#    - Format: **Section Title**
#    - Must be on its own line
#    - Add ONE blank line before it
#    - Add ONE blank line after it
#    - Never use ### or #

# 2. PARAGRAPHS - Use for explanations:
#    - Write 2-4 complete sentences per paragraph
#    - Add ONE blank line between paragraphs
#    - Do NOT start paragraphs with bullets

# 3. BULLET LISTS - Use only for listing items:
#    - Add ONE blank line before the list
#    - Format each bullet: - Item text
#    - Add ONE blank line after the list
#    - Use bullets for 3+ related items only

# EXAMPLE OF CORRECT FORMAT:

# **Consultation**

# Consultation involves seeking advice from community members on specific issues. The Health Department shares information and seeks feedback but retains final decision-making authority.

# Key aspects include:

# - Information sharing without full incorporation of input
# - Feedback is considered but may not influence decisions
# - Health Department retains ultimate authority

# **Collaboration**

# Collaboration involves working together as equal partners. Decisions are made through consensus between all parties.

# WHAT NOT TO DO:
# - Do NOT use bullets for every sentence
# - Do NOT put bullets before headings
# - Do NOT write one-sentence paragraphs followed by bullets
# - Do NOT use ---, ###, or other special characters

# CONTENT RULES:
# - Answer using ONLY the provided context
# - If not in context: "I could not find information in the knowledge base about that."
# - Be clear, professional, and well-structured"""

#             user_message = f"""
# CONTEXT from Knowledge Base:

# {context}

# USER QUESTION:

# {user_prompt}

# Please provide a comprehensive, well-formatted answer using the context above. Structure your response with:
# - Clear headings for main concepts
# - Explanatory paragraphs
# - Bullet points for key details
# - Proper spacing and line breaks

# Remember: Do NOT use ---, ###, or any special markdown characters in your response.
# """



#             # Stream response using Ollama
#             response_stream = self.ollama_client.chat(
#                 model=self.model_name,
#                 messages=[
#                     {'role': 'system', 'content': system_prompt},
#                     {'role': 'user', 'content': user_message}
#                 ],
#                 stream=True,
#                 options={
#                     'temperature': 0.3,
#                     'top_p': 0.9,
#                     'repeat_penalty': 1.2,
#                     'num_ctx': 4096,
#                 }
#             )
            
#             # Stream the response
#             for chunk in response_stream:
#                 if chunk['message']['content']:
#                     yield chunk['message']['content']

#         except Exception as e:
#             logger.error(f"Error generating streaming response with Ollama: {str(e)}", exc_info=True)
#             yield "I'm sorry, there was an error processing your request."

#     # def generate_response(self, messages):
#     #     try:
#     #         # Format prompt
#     #         user_prompt = messages[-1].content  # Assuming the last message is the user's
#     #         formatted_prompt = f"### Instruction:\n{user_prompt}\n\n### Response:\n"
#     #
#     #         inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)
#     #         from transformers import TextStreamer
#     #
#     #         # Assuming you've set up the tokenizer and model properly.
#     #         streamer = TextStreamer(self.tokenizer)
#     #
#     #         output = self.model.generate(
#     #             **inputs,
#     #             max_new_tokens=256,
#     #             do_sample=True,
#     #             top_p=0.95,
#     #             temperature=0.7,
#     #             pad_token_id=self.tokenizer.pad_token_id,
#     #             eos_token_id=self.tokenizer.eos_token_id,
#     #             streamer=streamer
#     #         )
#     #
#     #         response = self.tokenizer.decode(output[0], skip_special_tokens=True)
#     #         print("🧠 Model output:", response)
#     #         return response.split("### Response:")[-1].strip()
#     #
#     #     except Exception as e:
#     #         print("❌ Error generating response:", e)
#     #         return "I apologize, but I couldn't generate a meaningful response. Please try rephrasing your question."

import PyPDF2
import numpy as np
import faiss
import pickle
import os
import threading
import re
from sentence_transformers import SentenceTransformer
import ollama
from django.conf import settings
from .models import DocumentChunk, EmbeddingIndex
import logging
from typing import List, Dict, Generator, Optional
import asyncio
import json
from django.http import StreamingHttpResponse
import time

logger = logging.getLogger(__name__)


class PDFProcessingService:
    def __init__(self):
        self.chunk_size = 512
        self.chunk_overlap = 50

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
            
        # Use the best embedding model for improved accuracy and retrieval
        self.model = SentenceTransformer('BAAI/bge-large-en-v1.5')
        self.dimension = 1024
        self.index_path = os.path.join(settings.MEDIA_ROOT, 'faiss_index.bin')
        self.mapping_path = os.path.join(settings.MEDIA_ROOT, 'chunk_mapping.pkl')
        self.initialized = True
        logger.info(f"Initialized EmbeddingService with BAAI/bge-large-en-v1.5 (dim={self.dimension})")

    def create_embedding(self, text):
        """Create embedding for given text with query prefix for BGE model"""
        prefixed_text = f"Represent this sentence for searching relevant passages: {text}"
        return self.model.encode([prefixed_text], convert_to_tensor=False)[0]
    
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
            embeddings_array = np.array(embeddings).astype('float32')
            index = faiss.IndexFlatIP(self.dimension)
            faiss.normalize_L2(embeddings_array)
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

    def search_similar_chunks(self, query_text, top_k=40, similarity_threshold=0.4):
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
            search_k = min(top_k * 3, len(chunk_mapping))
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

    def search_similar_chunks_enhanced(self, query_text, top_k=40, similarity_threshold=0.3):
        """Enhanced search with query expansion for comparative queries and better results"""
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

            # Detect if this is a comparative query (contains "vs", "versus", "compared to", etc.)
            comparative_patterns = ['vs', 'versus', 'compared to', 'difference between', 'vs.', 'compare']
            is_comparative = any(pattern in query_text.lower() for pattern in comparative_patterns)
            
            all_chunks = []
            
            if is_comparative:
                logger.info(f"Detected comparative query: {query_text}")
                
                # Extract the concepts being compared
                query_lower = query_text.lower()
                
                # Split on common comparison patterns
                concepts = []
                for pattern in ['vs', 'versus', 'vs.']:
                    if pattern in query_lower:
                        parts = query_lower.split(pattern)
                        if len(parts) >= 2:
                            concepts = [part.strip() for part in parts[:2]]
                            break
                
                # If no clear split, try "difference between X and Y"
                if not concepts and 'difference between' in query_lower:
                    parts = query_lower.replace('difference between', '').split(' and ')
                    if len(parts) >= 2:
                        concepts = [part.strip() for part in parts[:2]]
                
                # Search for each concept separately and combine results
                if concepts:
                    logger.info(f"Searching for concepts: {concepts}")
                    
                    for concept in concepts:
                        if concept.strip():
                            concept_results = self._search_single_concept(
                                concept.strip(), 
                                index, 
                                chunk_mapping, 
                                top_k//2,  # Split the results between concepts
                                similarity_threshold * 0.8  # Lower threshold for individual concepts
                            )
                            all_chunks.extend(concept_results)
                    
                    # Also search the full query
                    full_query_results = self._search_single_concept(
                        query_text, 
                        index, 
                        chunk_mapping, 
                        top_k//3, 
                        similarity_threshold
                    )
                    all_chunks.extend(full_query_results)
                else:
                    # Fallback to normal search if concept extraction fails
                    all_chunks = self._search_single_concept(
                        query_text, 
                        index, 
                        chunk_mapping, 
                        top_k, 
                        similarity_threshold
                    )
            else:
                # Normal single concept search
                all_chunks = self._search_single_concept(
                    query_text, 
                    index, 
                    chunk_mapping, 
                    top_k, 
                    similarity_threshold
                )
            
            # Remove duplicates and sort by similarity
            seen_chunk_ids = set()
            unique_chunks = []
            for chunk_data in all_chunks:
                chunk_id = chunk_data['chunk'].id
                if chunk_id not in seen_chunk_ids:
                    seen_chunk_ids.add(chunk_id)
                    unique_chunks.append(chunk_data)
            
            # Sort by similarity score (descending)
            unique_chunks.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Return top results
            result_chunks = unique_chunks[:top_k]
            logger.info(f"Enhanced search found {len(result_chunks)} unique chunks for query: {query_text}")
            return result_chunks

        except Exception as e:
            logger.error(f"Error in enhanced search: {str(e)}", exc_info=True)
            # Fallback to regular search
            return self.search_similar_chunks(query_text, top_k, similarity_threshold)
    
    def _search_single_concept(self, concept_text, index, chunk_mapping, top_k, similarity_threshold):
        """Helper method to search for a single concept"""
        try:
            # Create query embedding
            query_embedding = self.create_embedding(concept_text)
            query_vector = np.array([query_embedding]).astype('float32')
            faiss.normalize_L2(query_vector)

            # Search with more results to filter by threshold
            search_k = min(top_k * 3, len(chunk_mapping))
            scores, indices = index.search(query_vector, search_k)

            # Get corresponding chunks with filtering
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
                
                # Stop if we have enough results
                if len(similar_chunks) >= top_k:
                    break

            return similar_chunks
            
        except Exception as e:
            logger.error(f"Error searching single concept '{concept_text}': {str(e)}")
            return []


def post_process_response(text: str) -> str:
    """
    Clean up model output to ensure proper formatting before markdown conversion.
    Fixes common formatting issues from LLM responses.
    """
    if not text or not text.strip():
        return text
    
    lines = text.split('\n')
    cleaned_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines for now
        if not line:
            i += 1
            continue
        
        # Check if this is a heading (bold text alone on line)
        is_heading = bool(re.match(r'^\*\*[^*]+\*\*$', line))
        
        # Check if this is a bullet point
        is_bullet = line.startswith('- ') or line.startswith('* ')
        
        if is_heading:
            # Add blank line before heading (if not first line)
            if cleaned_lines and cleaned_lines[-1] != '':
                cleaned_lines.append('')
            
            # Add the heading
            cleaned_lines.append(line)
            
            # Add blank line after heading
            cleaned_lines.append('')
        
        elif is_bullet:
            # Normalize bullet to dash
            if line.startswith('* '):
                line = '- ' + line[2:]
            
            # Check if previous line was not a bullet - add blank line before list
            if cleaned_lines and not cleaned_lines[-1].startswith('- ') and cleaned_lines[-1] != '':
                cleaned_lines.append('')
            
            cleaned_lines.append(line)
            
            # Check if next line is not a bullet - add blank line after list
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith('-') and not next_line.startswith('*'):
                    # Check if it's end of list
                    if not re.match(r'^\*\*[^*]+\*\*$', next_line):
                        # Next line is regular text, add spacing after list
                        pass
                    else:
                        # Next line is heading, spacing will be added by heading logic
                        pass
            
            # Add blank line after last bullet if next is not bullet
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith('-') and not next_line.startswith('*'):
                    cleaned_lines.append('')
        
        else:
            # Regular paragraph text
            cleaned_lines.append(line)
            
            # Add blank line after paragraph if next line is heading or bullet
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line:
                    next_is_heading = bool(re.match(r'^\*\*[^*]+\*\*$', next_line))
                    next_is_bullet = next_line.startswith('-') or next_line.startswith('*')
                    
                    if next_is_heading or next_is_bullet:
                        cleaned_lines.append('')
        
        i += 1
    
    # Join and clean up excessive blank lines
    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()


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
            
        # Use Ollama for optimized model management
        self.ollama_client = ollama.Client()
        self.model_name = "phi4-mini:latest"
        
        # Test Ollama connection
        try:
            models = self.ollama_client.list()
            available_models = [m.model for m in models['models']]
            if self.model_name in available_models:
                logger.info(f"✓ Ollama connected. Using {self.model_name}")
                self.ollama_available = True
            else:
                logger.error(f"Model {self.model_name} not found in Ollama. Available: {available_models}")
                self.ollama_available = False
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            self.ollama_available = False
        
        self.embedding_service = EmbeddingService()
        self.initialized = True
        logger.info("ChatService initialized with Ollama backend")

    def load_model(self):
        """Load model through Ollama - no manual loading needed"""
        if not self.ollama_available:
            raise Exception("Ollama not available. Please ensure Ollama is running and phi4-mini is installed.")
        
        # Test the model
        try:
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt="Test",
                stream=False
            )
            logger.info(f"✓ {self.model_name} model ready via Ollama")
        except Exception as e:
            logger.error(f"Error testing Ollama model: {str(e)}")
            raise

    def get_relevant_context(self, query: str, top_k: int = 5) -> str:
        """Retrieve relevant context from documents using RAG"""
        try:
            similar_chunks = self.embedding_service.search_similar_chunks(query, top_k=top_k)
            
            if not similar_chunks:
                logger.info("No relevant chunks found")
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
        """Format a context string from provided similar chunks"""
        try:
            if not similar_chunks:
                return ""
            context_parts = []
            for chunk_data in similar_chunks:
                chunk = chunk_data['chunk']
                context_parts.append(
                    f"Document: {chunk.document.title}\nContent: {chunk.content}"
                )
            return "\n\n".join(context_parts)
        except Exception as e:
            logger.warning(f"Error formatting context from chunks: {e}")
            return ""
    
    def generate_response(self, messages, similar_chunks=None):
        """Generate response with RAG (Retrieval-Augmented Generation)"""
        try:
            if not self.ollama_available:
                self.load_model()
            
            user_prompt = messages[-1].content
            
            # Get relevant context from documents
            context = self._format_context_from_chunks(similar_chunks) if similar_chunks else self.get_relevant_context(user_prompt)
            
            # Require KB context
            if not context:
                return "I could not find information in the knowledge base about that. Please rephrase or upload relevant documents."
            
            # System prompt for clean, structured answers
            system_prompt = """You are a knowledge base assistant providing clear, well-structured answers.

CRITICAL RULES - KNOWLEDGE BASE ONLY:
1. STRICTLY use ONLY information from the CONTEXT provided below
2. NEVER use your own training knowledge or general knowledge
3. If information is not explicitly mentioned in the CONTEXT, say: "I could not find that information in the knowledge base"
4. Do NOT make assumptions or inferences beyond what's stated in the CONTEXT
5. Do NOT add information from outside the provided CONTEXT
6. NEVER mention what's in or not in the context
7. Do NOT repeat the question back
8. NEVER use Q&A format with "Question:" and "Answer:" labels
9. NEVER use mechanical structures like "Pros:", "Cons:", "Use when:", or similar labels
10. Do NOT mention document names, citations, page numbers, or ANY references whatsoever
11. NEVER include parenthetical citations like (Document: 16), (Content: 8), (Source: X), or any form of attribution
12. Do NOT use phrases like "Content: 16", "Document: 8", "Source:", "According to", or similar references
13. CRITICAL: Remove ALL content references - no "(Content: 8)", no "(Content: 16)", no citations of any kind
14. Present ALL information as direct, natural facts without any attribution or citation markers
15. Write as if the information is common knowledge, not sourced from specific documents
16. If you see content references in the context, ignore them and do NOT repeat them
17. Write in natural, flowing prose without mechanical formatting
18. Generate response in clean, semantic HTML format with proper spacing
19. Write complete, well-formed sentences with proper grammar
20. Do NOT include any HTML links or anchor tags that would cause underlining

HTML FORMATTING GUIDELINES:
- Use <h3> tags for main topic headings
- Use <p> tags for complete, coherent paragraphs (2-4 sentences each)
- Use <ul> and <li> tags for bullet points
- Ensure proper sentence structure and spacing
- No awkward line breaks or fragment sentences
- Each paragraph should flow naturally
- Proper punctuation and spacing

EXAMPLES:

User asks: "When should I use outreach vs collaboration?"

GOOD answer (natural and flowing): 
"<h3>Outreach</h3>
<p>Outreach is most effective when you need to quickly disseminate public health information during emergencies or infectious disease outbreaks. This approach allows for rapid, wide-reaching communication to communities and can be implemented with relatively fewer resources. The communication flows primarily from the Health Department to the community, making it ideal for urgent information sharing.</p>

<h3>Collaboration</h3>
<p>Collaboration becomes valuable when your project requires deeper stakeholder involvement and bidirectional communication. This method builds stronger relationships over time through shared decision-making and ongoing dialogue with community partners. While it requires more time and resources, collaboration leads to better outcomes for complex public health challenges.</p>"

BAD examples (NEVER DO):
- "Question Q: When should I use outreach? Answer: Use outreach when..."
- "Pros: Quick dissemination; Cons: Limited engagement"
- "Use Outreach when: - Emergency situations"
- "...such as infectious disease outbreaks (Content: 16)"
- "...like injection drug users in opioid use cases (Content: 8)"
- Any citations, references, or parenthetical attributions
- Any mechanical formatting with labels and structured lists

GOOD approach: Write naturally as flowing paragraphs that directly address the topic without mechanical structures or Q&A formatting.

Generate clean, properly structured HTML with complete sentences and good formatting.

REMEMBER: You are ONLY a knowledge base assistant. Your ONLY job is to extract and present information that exists in the provided CONTEXT. You must NOT use any external knowledge, training data, or make educated guesses. If it's not explicitly in the CONTEXT, admit you don't have that information.

CRITICAL: Write responses as natural, flowing text without ANY citations, references, or attributions. Never mention where information comes from - just state facts directly and naturally.

FINAL REMINDER: Write like you're having a professional conversation. NO Q&A format, NO "Pros/Cons" lists, NO mechanical structures. NO CITATIONS OR REFERENCES OF ANY KIND - remove all "(Content: X)" references completely. Just natural, informative paragraphs that directly address what the user asked about. Use only plain text within HTML tags - no links or special formatting that would cause underlining."""


            user_message = f"""Context from documents:

{context}

Question: {user_prompt}

IMPORTANT: Provide a clear, well-structured answer in HTML format using STRICTLY AND EXCLUSIVELY the context provided above. Do NOT use any information from your training data or general knowledge. If the answer is not in the context above, say "I could not find that information in the knowledge base." 

Write as natural, flowing paragraphs using <h3> for headings and <p> for complete paragraphs. NEVER use Q&A format, "Pros:", "Cons:", or mechanical structures. 

ABSOLUTELY CRITICAL - CITATION REMOVAL: 
- NO citations, references, or attributions of ANY kind
- NO "(Content: 8)", NO "(Content: 16)", NO "(Content: X)"
- NO "(Document: X)", NO "(Source: X)", NO "(Page X)"
- If you see ANY parenthetical references in the context, DO NOT include them in your response
- Remove all citation patterns completely
- Write as natural conversation without any academic references
- Present information as if it's common knowledge

Do NOT repeat the question. Write naturally as if stating facts in a conversation."""

            # Generate response using Ollama
            response = self.ollama_client.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message}
                ],
                stream=False,
                options={
                    'temperature': 0.3,
                    'top_p': 0.9,
                    'top_k': 40,
                    'repeat_penalty': 1.2,
                    'num_ctx': 4096,
                    'num_predict': 512,  # Increased to allow for multiple paragraph responses
                }
            )
            
            generated_text = response['message']['content'].strip()
            
            # Skip post-processing since we're now using HTML format
            # generated_text = post_process_response(generated_text)
            
            if not generated_text:
                return "I'm here to help! How can I assist you today?"
                
            return generated_text

        except Exception as e:
            logger.error(f"Error generating response with Ollama: {str(e)}")
            return "I'm sorry, there was an error processing your request."
    
    def generate_response_stream(self, messages, similar_chunks=None) -> Generator[str, None, None]:
        """Generate streaming response with RAG using Ollama backend"""
        try:
            if not self.ollama_available:
                self.load_model()
            
            user_prompt = messages[-1].content
            
            # Get relevant context from documents
            context = self._format_context_from_chunks(similar_chunks) if similar_chunks else self.get_relevant_context(user_prompt)
            
            # Require KB context
            if not context:
                yield "I could not find information in the knowledge base about that. Please rephrase or upload relevant documents."
                return
            
            # System prompt for clean HTML responses with better formatting
            system_prompt = """You are a knowledge base assistant providing clear, well-structured answers in HTML format.

CRITICAL RULES - KNOWLEDGE BASE ONLY:
1. STRICTLY use ONLY information from the CONTEXT provided below
2. NEVER use your own training knowledge or general knowledge
3. If information is not explicitly mentioned in the CONTEXT, say: "I could not find that information in the knowledge base"
4. Do NOT make assumptions or inferences beyond what's stated in the CONTEXT
5. Do NOT add information from outside the provided CONTEXT
6. NEVER mention what's in or not in the context
7. Do NOT repeat the question back
8. NEVER use Q&A format with "Question:" and "Answer:" labels
9. NEVER use mechanical structures like "Pros:", "Cons:", "Use when:", or similar labels
10. Do NOT mention document names, citations, page numbers, or ANY references whatsoever
11. NEVER include parenthetical citations like (Document: 16), (Content: 8), (Source: X), or any form of attribution
12. Do NOT use phrases like "Content: 16", "Document: 8", "Source:", "According to", or similar references
13. CRITICAL: Remove ALL content references - no "(Content: 8)", no "(Content: 16)", no citations of any kind
14. Present ALL information as direct, natural facts without any attribution or citation markers
15. Write as if the information is common knowledge, not sourced from specific documents
16. If you see content references in the context, ignore them and do NOT repeat them
17. Write in natural, flowing prose without mechanical formatting
18. Generate response in clean, semantic HTML format with proper spacing
19. Write complete, well-formed sentences with proper grammar
20. Do NOT include any HTML links or anchor tags that would cause underlining

HTML FORMATTING GUIDELINES:
- Use <h3> tags for main topic headings
- Use <p> tags for complete, coherent paragraphs (2-4 sentences each)
- Use <ul> and <li> tags for bullet points
- Ensure proper sentence structure and spacing
- No awkward line breaks or fragment sentences
- Each paragraph should flow naturally
- Proper punctuation and spacing

EXAMPLES:

User asks: "When should I use outreach vs collaboration?"

GOOD answer (natural and flowing): 
"<h3>Outreach</h3>
<p>Outreach is most effective when you need to quickly disseminate public health information during emergencies or infectious disease outbreaks. This approach allows for rapid, wide-reaching communication to communities and can be implemented with relatively fewer resources. The communication flows primarily from the Health Department to the community, making it ideal for urgent information sharing.</p>

<h3>Collaboration</h3>
<p>Collaboration becomes valuable when your project requires deeper stakeholder involvement and bidirectional communication. This method builds stronger relationships over time through shared decision-making and ongoing dialogue with community partners. While it requires more time and resources, collaboration leads to better outcomes for complex public health challenges.</p>"

BAD examples (NEVER DO):
- "Question Q: When should I use outreach? Answer: Use outreach when..."
- "Pros: Quick dissemination; Cons: Limited engagement"
- "Use Outreach when: - Emergency situations"
- "...such as infectious disease outbreaks (Content: 16)"
- "...like injection drug users in opioid use cases (Content: 8)"
- Any citations, references, or parenthetical attributions
- Any mechanical formatting with labels and structured lists

GOOD approach: Write naturally as flowing paragraphs that directly address the topic without mechanical structures or Q&A formatting.

Generate clean, properly structured HTML with complete sentences and good formatting.

REMEMBER: You are ONLY a knowledge base assistant. Your ONLY job is to extract and present information that exists in the provided CONTEXT. You must NOT use any external knowledge, training data, or make educated guesses. If it's not explicitly in the CONTEXT, admit you don't have that information.

CRITICAL: Write responses as natural, flowing text without ANY citations, references, or attributions. Never mention where information comes from - just state facts directly and naturally.

FINAL REMINDER: Write like you're having a professional conversation. NO Q&A format, NO "Pros/Cons" lists, NO mechanical structures. NO CITATIONS OR REFERENCES OF ANY KIND - remove all "(Content: X)" references completely. Just natural, informative paragraphs that directly address what the user asked about. Use only plain text within HTML tags - no links or special formatting that would cause underlining."""


            user_message = f"""Context from documents:

{context}

Question: {user_prompt}

IMPORTANT: Provide a clear, well-structured answer in HTML format using STRICTLY AND EXCLUSIVELY the context provided above. Do NOT use any information from your training data or general knowledge. If the answer is not in the context above, say "I could not find that information in the knowledge base." 

Write as natural, flowing paragraphs using <h3> for headings and <p> for complete paragraphs. NEVER use Q&A format, "Pros:", "Cons:", or mechanical structures. 

ABSOLUTELY CRITICAL - CITATION REMOVAL: 
- NO citations, references, or attributions of ANY kind
- NO "(Content: 8)", NO "(Content: 16)", NO "(Content: X)"
- NO "(Document: X)", NO "(Source: X)", NO "(Page X)"
- If you see ANY parenthetical references in the context, DO NOT include them in your response
- Remove all citation patterns completely
- Write as natural conversation without any academic references
- Present information as if it's common knowledge

Do NOT repeat the question. Write naturally as if stating facts in a conversation."""

            # Stream response using Ollama - yield tokens in REAL-TIME
            response_stream = self.ollama_client.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message}
                ],
                stream=True,
                options={
                    'temperature': 0.3,
                    'top_p': 0.9,
                    'top_k': 40,
                    'repeat_penalty': 1.2,
                    'num_ctx': 4096,
                    'num_predict': 512,  # Increased to allow for multiple paragraph responses
                }
            )
            
            # Stream tokens in real-time (don't collect first, stream directly!)
            for chunk in response_stream:
                if chunk['message']['content']:
                    token = chunk['message']['content']
                    yield token

        except Exception as e:
            logger.error(f"Error generating streaming response with Ollama: {str(e)}", exc_info=True)
            yield "I'm sorry, there was an error processing your request."