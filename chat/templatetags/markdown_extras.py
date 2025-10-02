import re
from django import template
import markdown
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='markdownify')
def markdownify(text):
    # Add blank line before any line starting with a dash or number (for lists)
    text = re.sub(r'([^\n])\n(- )', r'\1\n\n\2', text)
    text = re.sub(r'([^\n])\n(\d+\. )', r'\1\n\n\2', text)
    
    # Add blank line before headings
    text = re.sub(r'([^\n])\n(#{1,6} )', r'\1\n\n\2', text)
    
    # Fix bold headings spacing - ensure blank lines before and after
    text = re.sub(r'([^\n])\n(\*\*[^*]+\*\*)', r'\1\n\n\2', text)
    text = re.sub(r'(\*\*[^*]+\*\*)\n([^\n])', r'\1\n\n\2', text)
    
    # Fix concatenated bullet points (common issue with AI responses)
    text = re.sub(r'(\.)(\s*-\s)', r'\1\n\n\2', text)
    text = re.sub(r'([a-z])\s*-\s', r'\1\n\n- ', text)
    
    # Clean up multiple consecutive newlines (but preserve double newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    html = markdown.markdown(text, extensions=['extra'])
    return mark_safe(html)
