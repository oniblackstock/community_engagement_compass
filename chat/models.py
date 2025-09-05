import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class PDFDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(PDFDocument, related_name='chunks', on_delete=models.CASCADE)
    content = models.TextField()
    chunk_index = models.IntegerField()
    page_number = models.IntegerField(null=True, blank=True)
    embedding_vector = models.BinaryField(null=True, blank=True)  # Store serialized embedding

    class Meta:
        ordering = ['document', 'chunk_index']
        unique_together = ['document', 'chunk_index']

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_name = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-updated_at']

    def update_title_from_message(self, message_content):
        """Update the chat title based on the first message"""
        # Truncate the message if it's too long and add ellipsis
        max_length = 50
        title = message_content[:max_length]
        if len(message_content) > max_length:
            title = title.rsplit(' ', 1)[0] + '...'

        self.session_name = title
        self.save()
        return self.session_name

    def __str__(self):
        return self.session_name


class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    sources = models.ManyToManyField(DocumentChunk, blank=True)  # Track which chunks were used

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."

    @property
    def is_user(self):
        """Return True if message is from user"""
        return self.message_type == 'user'

    @property
    def is_assistant(self):
        """Return True if message is from assistant"""
        return self.message_type == 'assistant'

    @property
    def is_system(self):
        """Return True if message is system message"""
        return self.message_type == 'system'


@receiver(post_save, sender=ChatMessage)
def update_session_title(sender, instance, created, **kwargs):
    """Update chat session title based on the first user message"""
    if created and instance.message_type == 'user':
        # Count messages in the session
        message_count = ChatMessage.objects.filter(session=instance.session).count()

        # If this is the first message in the session
        if message_count == 1:
            # Create a title from the message content
            title = instance.content[:50].strip()
            if len(instance.content) > 50:
                title += "..."

            # Update the session name
            instance.session.session_name = title
            instance.session.save()


class EmbeddingIndex(models.Model):
    """Stores metadata about the FAISS index"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    index_file = models.CharField(max_length=255)  # Path to FAISS index file
    dimension = models.IntegerField(default=768)
    total_vectors = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
