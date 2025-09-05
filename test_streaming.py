#!/usr/bin/env python3
"""
Test streaming functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from chat.services import ChatService
from chat.models import ChatSession, ChatMessage
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_streaming():
    """Test streaming response generation"""
    print("🧪 Testing streaming response...")
    
    try:
        chat_service = ChatService()
        
        # Create a test session and message
        session = ChatSession.objects.create(session_name="Test Session")
        user_message = ChatMessage.objects.create(
            session=session,
            message_type='user',
            content="Hello, how are you?"
        )
        
        messages = [user_message]
        
        print("📤 Generating streaming response...")
        print("Response: ", end="", flush=True)
        
        # Test streaming
        for token in chat_service.generate_response_stream(messages):
            print(token, end="", flush=True)
        
        print("\n✅ Streaming test completed successfully!")
        
        # Clean up
        session.delete()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Streaming test failed: {str(e)}")
        logger.error(f"Streaming test error: {str(e)}", exc_info=True)
        return False

def main():
    """Run streaming test"""
    print("🚀 Streaming Test")
    print("=" * 30)
    
    success = test_streaming()
    
    if success:
        print("\n🎉 Streaming is working correctly!")
    else:
        print("\n❌ Streaming test failed.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
