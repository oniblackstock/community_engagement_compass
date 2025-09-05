#!/usr/bin/env python3
"""
Test script to check model loading and device usage
"""
import os
import sys
import django
import torch
import time

# Setup Django
sys.path.append('/home/conovo-ai/Documents/knowledgeassistant')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from chat.services import ChatService

def test_model_loading():
    print("=" * 50)
    print("TESTING MODEL LOADING AND DEVICE USAGE")
    print("=" * 50)
    
    # Check PyTorch and CUDA
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"Current device: {torch.cuda.current_device()}")
        print(f"Device name: {torch.cuda.get_device_name()}")
    else:
        print("CUDA not available - will use CPU")
    
    print("\n" + "=" * 50)
    print("INITIALIZING CHAT SERVICE")
    print("=" * 50)
    
    # Initialize ChatService
    start_time = time.time()
    chat_service = ChatService()
    init_time = time.time() - start_time
    print(f"ChatService initialized in {init_time:.2f} seconds")
    print(f"Device: {chat_service.device}")
    
    print("\n" + "=" * 50)
    print("LOADING MODEL")
    print("=" * 50)
    
    # Load model
    start_time = time.time()
    chat_service.load_model()
    load_time = time.time() - start_time
    print(f"Model loaded in {load_time:.2f} seconds")
    
    if chat_service.model is not None:
        print(f"Model device: {next(chat_service.model.parameters()).device}")
        print(f"Model dtype: {next(chat_service.model.parameters()).dtype}")
    
    print("\n" + "=" * 50)
    print("TESTING GENERATION")
    print("=" * 50)
    
    # Test generation
    from chat.models import ChatSession, ChatMessage
    
    # Create a test session and message
    session = ChatSession.objects.create(session_name="Test Session")
    message = ChatMessage.objects.create(
        session=session,
        message_type='user',
        content="Hello, how are you?"
    )
    
    # Test generation
    start_time = time.time()
    response = chat_service.generate_response([message])
    gen_time = time.time() - start_time
    
    print(f"Generation completed in {gen_time:.2f} seconds")
    print(f"Response length: {len(response)} characters")
    print(f"Response: {response[:100]}...")
    
    # Clean up
    session.delete()
    
    print("\n" + "=" * 50)
    print("TEST COMPLETED")
    print("=" * 50)

if __name__ == "__main__":
    test_model_loading()

