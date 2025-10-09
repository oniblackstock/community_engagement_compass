import re
import logging
from django import template
import markdown
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)

register = template.Library()

@register.filter(name='markdownify')
def markdownify(text):
    """ChatGPT-style clean markdown formatting with proper parsing"""
    
    if not text or not text.strip():
        return mark_safe("")
    
    # Clean up the input text
    text = text.strip()
    
    # Apply comprehensive cleaning before markdown parsing
    text = _clean_markdown_text(text)
    
    try:
        # Use clean markdown processing with proper extensions
        html = markdown.markdown(text, extensions=[
            'extra',      # Tables, footnotes, abbreviations
            'nl2br',      # Newline to <br>
            'sane_lists', # Better list handling
        ])
        
        # Post-process to ensure clean output
        html = re.sub(r'<p>\s*</p>', '', html)  # Remove empty paragraphs
        html = re.sub(r'(<br\s*/?>\s*){2,}', '<br>', html)  # Remove multiple line breaks
        
        return mark_safe(html)
        
    except Exception as e:
        logger.error(f"Markdown processing failed: {e}")
        
        # Robust fallback with clean formatting
        return _fallback_format(text)


def _clean_markdown_text(text):
    """Extremely conservative cleaning to preserve author formatting.
    Only normalize obvious issues; do not inject or modify bold/heading syntax.
    """
    if not text:
        return ''

    # Remove horizontal rules (---) that shouldn't be visible in output
    text = re.sub(r'(?m)^---+\s*$', '', text)  # Remove horizontal rules on their own line
    text = re.sub(r'\s---+\s', ' ', text)  # Remove --- in middle of text
    
    # Remove special symbols and emojis that shouldn't be in responses
    text = re.sub(r'[✅❌]', '', text)  # Remove checkmarks and crosses
    
    # Convert hash headings (###) to bold headings (**)
    # text = re.sub(r'(?m)^#{1,6}\s+(.+)$', r'**\1**', text)
    # Ensure bold headings aren't jammed into paragraph text
    text = re.sub(r'(\*\*[^*\n]+\*\*)(\S)', r'\1\n\n\2', text)


    # Normalize unicode bullets to hyphens
    # text = re.sub(r'[•·▪▫‣⁃]', '-', text)

    # Convert inline " - " markers into list items on new lines
    # text = re.sub(r'([^\n])\s-\s', r'\1\n- ', text)

    # Convert leading '- ' bullets to '• ' to honor no-hyphen requirement
    # text = re.sub(r'(?m)^-\s+', '• ', text)

    # CRITICAL: Ensure bold headings have proper line breaks after them
    # This handles both cases: bold with newline, and bold directly followed by text
    # First, ensure bold headings followed directly by text get a newline
    text = re.sub(r'(\*\*[^*\n]+\*\*)\s+([A-Z])', r'\1\n\n\2', text)
    # Then ensure bold headings with only one newline get two
    text = re.sub(r'(?m)^(\*\*[^*\n]+\*\*)\n(?!\n)', r'\1\n\n', text)
    # Also handle bold headings that end with ? or : followed by text
    text = re.sub(r'(\*\*[^*]+[?:]\*\*)\s+([A-Za-z])', r'\1\n\n\2', text)

    # Collapse excessive blank lines (keep at most two) and spaces
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    return text.strip()


def _fallback_format(text):
    """Fallback formatting if markdown library fails - converts markdown to HTML manually"""
    
    # Clean the text using minimal cleaning
    text = _clean_markdown_text(text)
    
    # Escape HTML to prevent injection
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Convert markdown syntax to HTML
    # Bold text: **text** -> <strong>text</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Headings: ### Text -> <h3>Text</h3>
    text = re.sub(r'^(#{1,6})\s+(.+)$', 
                 lambda m: f'<h{len(m.group(1))}>{m.group(2).strip()}</h{len(m.group(1))}>', 
                 text, flags=re.MULTILINE)
    
    # Process lines for lists and paragraphs
    lines = text.split('\n')
    result_lines = []
    in_list = False
    current_paragraph = []
    
    for line in lines:
        line = line.strip()
        
        # Bullet point line
        if re.match(r'^[-*]\s+', line):
            if current_paragraph:
                result_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            content = re.sub(r'^[-*]\s+', '', line)
            result_lines.append(f'<li>{content}</li>')
        
        # Numbered list line
        elif re.match(r'^\d+\.\s+', line):
            if current_paragraph:
                result_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            content = re.sub(r'^\d+\.\s+', '', line)
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            result_lines.append(f'<li>{content}</li>')
        
        # Empty line
        elif not line:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if current_paragraph:
                result_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
        
        # Already formatted HTML (headings)
        elif line.startswith('<'):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if current_paragraph:
                result_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
            result_lines.append(line)
        
        # Standalone bold text (treat as heading)
        elif re.match(r'^\*\*[^*]+\*\*$', line):
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            if current_paragraph:
                result_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
            # Convert to standalone strong element (will be styled as heading by CSS)
            heading_text = line[2:-2]  # Remove ** from start and end
            result_lines.append(f'<strong>{heading_text}</strong>')
        
        # Regular text line
        else:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            current_paragraph.append(line)
    
    # Close any open list
    if in_list:
        result_lines.append('</ul>')
    
    # Add any remaining paragraph
    if current_paragraph:
        result_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
    
    return mark_safe('\n'.join(result_lines))
 