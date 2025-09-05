#!/usr/bin/env python3
"""
Simple streaming test
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from chat.services import ChatService
from chat.models import ChatSession, ChatMessage

def test_simple_streaming():
    """Test simple streaming"""
    print("Testing streaming...")
    
    try:
        chat_service = ChatService()
        
        # Create test session and message
        session = ChatSession.objects.create(session_name="Test")
        message = ChatMessage.objects.create(
            session=session,
            message_type='user',
            content="Hello"
        )
        
        print("Generating response...")
        response = ""
        for token in chat_service.generate_response_stream([message]):
            response += token
            print(token, end="", flush=True)
        
        print(f"\n\nComplete response: {response}")
        print("✅ Streaming test completed!")
        
        # Cleanup
        session.delete()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_streaming()
