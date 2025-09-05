import PyPDF2
import numpy as np
import faiss
import pickle
import os
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
import torch
from django.conf import settings
from .models import DocumentChunk, EmbeddingIndex
import logging
import gc
import psutil
from functools import lru_cache
from typing import List, Dict, Any, Generator
import threading
import time
import os
import pickle
import numpy as np
import torch
from functools import lru_cache
from sentence_transformers import SentenceTransformer
import faiss
import logging

from django.conf import settings
from chat.models import DocumentChunk, EmbeddingIndex

logger = logging.getLogger(__name__)


class PDFProcessingService:
    def __init__(self):
        self.chunk_size = 512  # Optimal for your hardware
        self.chunk_overlap = 128
        self.max_workers = 8  # Utilize your 32GB RAM

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
        """Optimized chunking for better context"""
        chunks = []
        chunk_index = 0

        for page_data in text_pages:
            text = page_data['text']
            page_num = page_data['page']

            # Better sentence-aware chunking
            sentences = self._split_into_sentences(text)
            current_chunk = []
            current_length = 0

            for sentence in sentences:
                sentence_words = len(sentence.split())
                
                if current_length + sentence_words <= self.chunk_size:
                    current_chunk.append(sentence)
                    current_length += sentence_words
                else:
                    if current_chunk:
                        chunk_text = ' '.join(current_chunk)
                        chunks.append({
                            'content': chunk_text,
                            'page_number': page_num,
                            'chunk_index': chunk_index
                        })
                        chunk_index += 1
                    
                    # Smart overlap
                    overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else []
                    current_chunk = overlap_sentences + [sentence]
                    current_length = sum(len(s.split()) for s in current_chunk)

            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'page_number': page_num,
                    'chunk_index': chunk_index
                })
                chunk_index += 1

        return chunks

    def _split_into_sentences(self, text):
        """Better sentence splitting"""
        import re
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    def process_document(self, document):
        """Batch processing optimized for your hardware"""
        try:
            text_pages = self.extract_text_from_pdf(document.file.path)
            chunks = self.create_chunks(text_pages)
            
            # Bulk create chunks
            chunk_objects = []
            for chunk_data in chunks:
                chunk_objects.append(DocumentChunk(
                    document=document,
                    content=chunk_data['content'],
                    page_number=chunk_data['page_number'],
                    chunk_index=chunk_data['chunk_index']
                ))
            
            created_chunks = DocumentChunk.objects.bulk_create(chunk_objects, batch_size=100)
            
            # Generate embeddings in optimized batches
            embedding_service = EmbeddingService()
            embedding_service.batch_create_embeddings(created_chunks)
            
            # Update FAISS index
            embedding_service.update_faiss_index()
            
            document.processed = True
            document.processing_error = None
            document.save()
            
            logger.info(f"Successfully processed document: {document.title} ({len(chunks)} chunks)")
            
        except Exception as e:
            document.processing_error = str(e)
            document.processed = False
            document.save()
            logger.error(f"Error processing document {document.title}: {str(e)}")
            raise




class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize embedding model with GPU optimization."""
        try:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self._model = SentenceTransformer('all-MiniLM-L6-v2', device=device)

            if device == 'cuda':
                torch.cuda.empty_cache()
                mem = torch.cuda.get_device_properties(0).total_memory / 1e9
                logger.info(f"Embedding model loaded on GPU ({mem:.1f} GB)")

            self.dimension = 384
            self.index_path = os.path.join(settings.MEDIA_ROOT, 'faiss_index.bin')
            self.mapping_path = os.path.join(settings.MEDIA_ROOT, 'chunk_mapping.pkl')

        except Exception as e:
            logger.exception("Failed to initialize EmbeddingService")
            raise

    @staticmethod
    def _is_valid_vector(vec):
        """Check if the embedding vector is valid."""
        return isinstance(vec, (list, np.ndarray)) and all(isinstance(x, (float, int)) for x in vec)

    @lru_cache(maxsize=1000)
    def create_embedding(self, text):
        """Create and return a single embedding."""
        try:
            embedding = self._model.encode([text], convert_to_numpy=True)[0]
            return embedding.astype(np.float32)
        except Exception as e:
            logger.exception("Error creating embedding")
            raise

    def batch_create_embeddings(self, chunks):
        """Batch embed document chunks."""
        try:
            if not chunks:
                return

            texts = [chunk.content for chunk in chunks]
            batch_size = 64
            updated_chunks = []

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_chunks = chunks[i:i + batch_size]

                embeddings = self._model.encode(
                    batch_texts,
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    show_progress_bar=len(texts) > 100
                )

                for chunk, embedding in zip(batch_chunks, embeddings):
                    if self._is_valid_vector(embedding):
                        chunk.embedding_vector = pickle.dumps(np.array(embedding, dtype=np.float32))
                        updated_chunks.append(chunk)
                    else:
                        logger.warning(f"Invalid embedding vector for chunk ID {chunk.id}")

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            DocumentChunk.objects.bulk_update(updated_chunks, ['embedding_vector'], batch_size=100)
            logger.info(f"Batch created embeddings for {len(updated_chunks)} chunks")

        except Exception as e:
            logger.exception("Error during batch embedding")
            raise

    def update_faiss_index(self):
        """Build or update the FAISS index from DB embeddings."""
        try:
            chunks = DocumentChunk.objects.filter(embedding_vector__isnull=False).only('id', 'embedding_vector')

            if not chunks.exists():
                logger.warning("No chunks with embeddings found")
                return

            embeddings = []
            chunk_mapping = []

            for chunk in chunks.iterator(chunk_size=1000):
                try:
                    embedding = pickle.loads(chunk.embedding_vector)
                    if self._is_valid_vector(embedding):
                        embeddings.append(np.array(embedding, dtype=np.float32))
                        chunk_mapping.append(chunk.id)
                except Exception as e:
                    logger.warning(f"Skipping invalid embedding for chunk ID {chunk.id}: {e}")

            if not embeddings:
                logger.warning("No valid embeddings found for indexing")
                return

            embeddings_array = np.vstack(embeddings).astype(np.float32)
            faiss.normalize_L2(embeddings_array)

            if len(embeddings_array) > 5000:
                nlist = min(256, len(embeddings_array) // 20)
                quantizer = faiss.IndexFlatIP(self.dimension)
                index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist, faiss.METRIC_INNER_PRODUCT)
                index.train(embeddings_array)
                index.nprobe = 32
            else:
                index = faiss.IndexFlatIP(self.dimension)

            index.add(embeddings_array)

            faiss.write_index(index, self.index_path)
            with open(self.mapping_path, 'wb') as f:
                pickle.dump(chunk_mapping, f, protocol=pickle.HIGHEST_PROTOCOL)

            # Update metadata
            EmbeddingIndex.objects.filter(is_active=True).update(is_active=False)
            EmbeddingIndex.objects.create(
                index_file=self.index_path,
                dimension=self.dimension,
                total_vectors=len(embeddings),
                is_active=True
            )

            logger.info(f"FAISS index updated with {len(embeddings)} vectors")

        except Exception as e:
            logger.exception("Error updating FAISS index")
            raise

    def search_similar_chunks(self, query_text, top_k=5):
        """Search FAISS for similar chunks to the query text."""
        try:
            if not os.path.exists(self.index_path) or not os.path.exists(self.mapping_path):
                logger.info("FAISS index or mapping not found")
                return []

            index = faiss.read_index(self.index_path)
            with open(self.mapping_path, 'rb') as f:
                chunk_mapping = pickle.load(f)

            query_embedding = self.create_embedding(query_text)
            query_vector = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_vector)

            if hasattr(index, 'nprobe'):
                index.nprobe = min(32, getattr(index, 'nlist', 32))

            scores, indices = index.search(query_vector, min(top_k, len(chunk_mapping)))

            valid_chunk_ids = [
                chunk_mapping[idx]
                for score, idx in zip(scores[0], indices[0])
                if 0 <= idx < len(chunk_mapping) and score > 0.2
            ]

            if not valid_chunk_ids:
                return []

            chunk_dict = {
                chunk.id: chunk
                for chunk in DocumentChunk.objects.filter(id__in=valid_chunk_ids).select_related('document')
            }

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if 0 <= idx < len(chunk_mapping) and score > 0.2:
                    chunk_id = chunk_mapping[idx]
                    chunk = chunk_dict.get(chunk_id)
                    if chunk:
                        results.append({'chunk': chunk, 'similarity': float(score)})

            logger.debug(f"Found {len(results)} similar chunks for query")
            return results

        except Exception as e:
            logger.exception("Error searching similar chunks")
            return []


class ChatService:
    _instance = None
    _model = None
    _tokenizer = None
    _device = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ChatService, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Optimized initialization for 8GB GPU + 32GB RAM"""
        try:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            model_path = os.path.join(settings.BASE_DIR, "models/phi-2")
            
            # Clear GPU cache before loading
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                use_fast=True
            )

            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            # Optimized model loading for your hardware
            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,  # Use half precision for 8GB GPU
                trust_remote_code=True,
                device_map="auto",
                low_cpu_mem_usage=True,
                max_memory={0: "7GB"},  # Reserve 1GB for other operations
                offload_folder="./offload",  # Use your 32GB RAM for offloading
                use_cache=True
            )
            
            self._model.eval()
            
            # Memory optimization
            if hasattr(torch, 'compile') and self._device == "cuda":
                try:
                    self._model = torch.compile(self._model, mode="reduce-overhead")
                    logger.info("Model compiled with torch.compile")
                except Exception as e:
                    logger.warning(f"torch.compile failed, continuing without: {str(e)}")
            
            # Log memory usage
            if torch.cuda.is_available():
                memory_allocated = torch.cuda.memory_allocated(0) / 1e9
                memory_reserved = torch.cuda.memory_reserved(0) / 1e9
                logger.info(f"GPU Memory - Allocated: {memory_allocated:.1f}GB, Reserved: {memory_reserved:.1f}GB")
            
            ram_usage = psutil.virtual_memory().percent
            logger.info(f"RAM Usage: {ram_usage:.1f}%")
            logger.info(f"Successfully loaded Phi-2 model on {self._device}")
            
        except Exception as e:
            logger.error(f"Error loading Phi-2 model: {str(e)}")
            raise

    def _format_context(self, messages, similar_chunks=None):
        """Optimized context formatting"""
        context_parts = []
        
        if similar_chunks:
            context_parts.append("Relevant context from documents:")
            for chunk_data in similar_chunks[:2]:  # Reduced to prevent memory issues
                chunk = chunk_data['chunk']
                context_parts.append(f"[From {chunk.document.title}, Page {chunk.page_number}]")
                context_parts.append(chunk.content[:400])  # Reduced chunk size
            context_parts.append("\nBased on the above context:")

        # Limit conversation history for memory efficiency
        recent_messages = messages[-6:] if len(messages) > 6 else messages
        for msg in recent_messages:
            role = "Human: " if msg.message_type == 'user' else "Assistant: "
            context_parts.append(f"{role}{msg.content}")
        
        context_parts.append("Assistant: ")
        return "\n".join(context_parts)

    def generate_response(self, messages, similar_chunks=None):
        """Memory-optimized response generation"""
        try:
            if self._model is None or self._tokenizer is None:
                raise RuntimeError("Model not loaded properly")

            conversation = self._format_context(messages, similar_chunks)
            
            # Tokenize with memory optimization
            inputs = self._tokenizer(
                conversation,
                return_tensors="pt",
                truncation=True,
                max_length=1280,  # Reduced for memory efficiency
                padding=False,
                add_special_tokens=True
            )

            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            input_length = inputs["input_ids"].shape[1]

            # Clear cache before generation
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=200,  # Reasonable limit
                    min_new_tokens=5,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    repetition_penalty=1.1,
                    pad_token_id=self._tokenizer.pad_token_id,
                    eos_token_id=self._tokenizer.eos_token_id,
                    use_cache=True
                    # Removed early_stopping as it's not valid
                )

            response = self._tokenizer.decode(
                outputs[0][input_length:],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            ).strip()

            return self._clean_response(response) or "I couldn't generate a meaningful response. Please rephrase your question."
            
        except torch.cuda.OutOfMemoryError:
            logger.error("CUDA out of memory - clearing cache and retrying with smaller context")
            torch.cuda.empty_cache()
            gc.collect()
            
            # Retry with minimal context
            try:
                return self._generate_fallback_response(messages[-2:])  # Use only last 2 messages
            except Exception as fallback_error:
                logger.error(f"Fallback generation failed: {str(fallback_error)}")
                return "I'm experiencing memory issues. Please try a shorter question or restart the session."
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I encountered an error while generating a response. Please try again."
        finally:
            # Always cleanup
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def _generate_fallback_response(self, messages):
        """Minimal memory fallback generation"""
        conversation = "\n".join([f"{'Human' if msg.message_type == 'user' else 'Assistant'}: {msg.content}" for msg in messages])
        conversation += "\nAssistant: "
        
        inputs = self._tokenizer(conversation, return_tensors="pt", max_length=512, truncation=True)
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.8,
                do_sample=True,
                pad_token_id=self._tokenizer.pad_token_id
            )
        
        return self._tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    def generate_response_stream(self, messages, similar_chunks=None) -> Generator[str, None, None]:
        """Streaming with memory management"""
        try:
            if self._model is None or self._tokenizer is None:
                raise RuntimeError("Model not loaded properly")

            conversation = self._format_context(messages, similar_chunks)
            
            inputs = self._tokenizer(
                conversation,
                return_tensors="pt",
                truncation=True,
                max_length=1280,
                padding=False
            )

            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            # Clear cache before streaming
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            streamer = TextIteratorStreamer(
                self._tokenizer,
                skip_prompt=True,
                skip_special_tokens=True
            )

            generation_kwargs = {
                **inputs,
                "max_new_tokens": 200,
                "temperature": 0.7,
                "do_sample": True,
                "top_p": 0.9,
                "streamer": streamer,
                "use_cache": True
            }

            thread = threading.Thread(target=self._model.generate, kwargs=generation_kwargs)
            thread.start()

            for token in streamer:
                if token:
                    yield token

            thread.join()

        except Exception as e:
            logger.error(f"Error in streaming: {str(e)}")
            yield "Streaming error occurred. Please try again."
        finally:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def _clean_response(self, response):
        """Clean up generated response"""
        if not response:
            return ""
        
        response = response.replace("Human:", "").replace("Assistant:", "")
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        
        # Remove repetitive lines
        seen = set()
        cleaned_lines = []
        for line in lines:
            if line not in seen:
                cleaned_lines.append(line)
                seen.add(line)
        
        return '\n'.join(cleaned_lines).strip()

    def clear_cache(self):
        """Comprehensive cache clearing"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()

    def get_memory_stats(self):
        """Get current memory usage"""
        stats = {}
        if torch.cuda.is_available():
            stats['gpu_allocated'] = torch.cuda.memory_allocated(0) / 1e9
            stats['gpu_reserved'] = torch.cuda.memory_reserved(0) / 1e9
        
        memory = psutil.virtual_memory()
        stats['ram_used'] = memory.used / 1e9
        stats['ram_percent'] = memory.percent
        
        return stats

class ChatService:
    _instance = None
    _model = None
    _tokenizer = None
    _device = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ChatService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize only once"""
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._initialize()
                    self._initialized = True

    def _initialize(self):
        """Optimized initialization with GPU memory protection"""
        try:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            model_path = os.path.join(settings.BASE_DIR, "models/phi-2")
            
            # Check if GPU has enough memory before loading
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.get_device_properties(0).total_memory
                allocated_memory = torch.cuda.memory_allocated(0)
                available_memory = gpu_memory - allocated_memory
                
                logger.info(f"GPU Memory - Total: {gpu_memory/1e9:.1f}GB, Available: {available_memory/1e9:.1f}GB")
                
                if available_memory < 2e9:  # Less than 2GB available
                    logger.warning("Insufficient GPU memory, falling back to CPU")
                    self._device = "cpu"
                else:
                    torch.cuda.empty_cache()
            
            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                use_fast=True
            )

            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            # Fixed model loading with correct parameter names
            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                dtype=torch.float16 if self._device == "cuda" else torch.float32,  # Fixed: was torch_dtype
                trust_remote_code=True,
                device_map="auto" if self._device == "cuda" else None,
                low_cpu_mem_usage=True,
                max_memory={0: "6GB"} if self._device == "cuda" else None,  # Conservative limit
                use_cache=True
            )
            
            self._model.eval()
            
            # Skip torch.compile for Python 3.12+
            if hasattr(torch, 'compile') and self._device == "cuda":
                import sys
                if sys.version_info < (3, 12):
                    try:
                        self._model = torch.compile(self._model, mode="reduce-overhead")
                        logger.info("Model compiled with torch.compile")
                    except Exception as e:
                        logger.warning(f"torch.compile failed: {str(e)}")
                else:
                    logger.info("Skipping torch.compile for Python 3.12+")
            
            # Log final memory usage
            if torch.cuda.is_available():
                memory_allocated = torch.cuda.memory_allocated(0) / 1e9
                memory_reserved = torch.cuda.memory_reserved(0) / 1e9
                logger.info(f"GPU Memory - Allocated: {memory_allocated:.1f}GB, Reserved: {memory_reserved:.1f}GB")
            
            ram_usage = psutil.virtual_memory().percent
            logger.info(f"RAM Usage: {ram_usage:.1f}%")
            logger.info(f"Successfully loaded Phi-2 model on {self._device}")
            
        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"CUDA out of memory during initialization: {str(e)}")
            logger.info("Falling back to CPU mode")
            
            # Clear GPU and retry on CPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self._device = "cpu"
            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                dtype=torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                use_cache=True
            )
            self._model.eval()
            logger.info("Successfully loaded Phi-2 model on CPU")
            
        except Exception as e:
            logger.error(f"Error loading Phi-2 model: {str(e)}")
            raise

    def load_model(self):
        """Compatibility method for apps.py"""
        # Model is already loaded in __init__, so just verify it's ready
        if self._model is None or self._tokenizer is None:
            logger.warning("Model not loaded, reinitializing...")
            self._initialize()
        logger.info("ChatService model ready")
    def generate_response_stream(self, messages, similar_chunks=None):
        """Simple streaming that works with Django dev server"""
        full_response = self.generate_response(messages, similar_chunks)
        
        # Split into words and yield them
        words = full_response.split()
        for i, word in enumerate(words):
            if i == 0:
                yield word
            else:
                yield " " + word
            time.sleep(0.05)  # Small delay for streaming effect

    def _format_context(self, messages, similar_chunks=None):
        """Efficient context formatting"""
        context_parts = []
        
        # Add relevant document context if available
        if similar_chunks:
            context_parts.append("Relevant context from documents:")
            for chunk_data in similar_chunks[:3]:  # Limit to top 3
                chunk = chunk_data['chunk']
                context_parts.append(f"[From {chunk.document.title}, Page {chunk.page_number}]")
                context_parts.append(chunk.content[:500])  # Limit chunk size
            context_parts.append("\nBased on the above context and conversation:")

        # Add conversation history (limit to last 10 messages)
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        for msg in recent_messages:
            role = "Human: " if msg.message_type == 'user' else "Assistant: "
            context_parts.append(f"{role}{msg.content}")
        
        context_parts.append("Assistant: ")
        return "\n".join(context_parts)

    def generate_response(self, messages, similar_chunks=None):
        """Optimized response generation"""
        try:
            if self._model is None or self._tokenizer is None:
                raise RuntimeError("Model not loaded properly")

            # Format conversation with context
            conversation = self._format_context(messages, similar_chunks)
            
            # Efficient tokenization
            inputs = self._tokenizer(
                conversation,
                return_tensors="pt",
                truncation=True,
                max_length=1536,  # Reduced context window
                padding=False,    # No padding for single input
                add_special_tokens=True
            )

            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            input_length = inputs["input_ids"].shape[1]

            # Optimized generation parameters
            with torch.no_grad():  # Disable gradient computation
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=256,     # Limit response length
                    min_new_tokens=10,      # Ensure minimum response
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,             # Use nucleus sampling
                    repetition_penalty=1.1,
                    pad_token_id=self._tokenizer.pad_token_id,
                    eos_token_id=self._tokenizer.eos_token_id,
                    use_cache=True,
                    early_stopping=True
                )

            # Efficient decoding
            response = self._tokenizer.decode(
                outputs[0][input_length:],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            ).strip()

            # Clean up response
            response = self._clean_response(response)
            
            return response or "I couldn't generate a meaningful response. Please rephrase your question."
            
        except torch.cuda.OutOfMemoryError:
            logger.error("CUDA out of memory")
            torch.cuda.empty_cache()
            return "I'm experiencing memory issues. Please try a shorter question."
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"I encountered an error while generating a response. Please try again."

    def _clean_response(self, response):
        """Clean up generated response"""
        # Remove common generation artifacts
        response = response.replace("Human:", "").replace("Assistant:", "")
        
        # Remove repetitive patterns
        lines = response.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip() and line not in cleaned_lines[-3:]:  # Avoid recent repetition
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()

    def clear_cache(self):
        """Clear GPU memory cache"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# Additional utility function for background processing
def process_document_async(document_id):
    """Process document in background task"""
    from .models import Document
    try:
        document = Document.objects.get(id=document_id)
        service = PDFProcessingService()
        service.process_document(document)
    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {str(e)}")