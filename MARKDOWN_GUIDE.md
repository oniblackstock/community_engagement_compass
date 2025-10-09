# Markdown Formatting Guide

## Quick Reference for Developers

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MARKDOWN FLOW                           │
└─────────────────────────────────────────────────────────────┘

1. AI GENERATION (services.py)
   ↓
   Ollama model → Produces markdown with clear formatting
   Example: "**Overview**\n\nText here.\n\n- Point 1\n- Point 2"
   
2. DATABASE STORAGE (views.py)
   ↓
   Save original markdown to ChatMessage.content (NO modification)
   Database: "**Overview**\n\nText here.\n\n- Point 1\n- Point 2"
   
3A. FRONTEND RENDER - STREAMING (chat.html + JavaScript)
   ↓
   Token by token → minimal cleaning → marked.js → HTML
   
3B. FRONTEND RENDER - PAGE LOAD (chat.html + markdown_extras.py)
   ↓
   DB content → minimal cleaning → markdown library → HTML
   
4. BROWSER DISPLAY
   ↓
   Properly formatted response with headings, lists, paragraphs
```

### Key Principles

1. **Minimal Intervention**: Only fix truly broken patterns
2. **Consistent Processing**: Backend and frontend use identical cleaning
3. **AI-First Quality**: Guide the model to produce clean markdown
4. **Database Integrity**: Store original markdown unchanged

### Markdown Cleaning Rules

#### ✅ DO Clean These:

```python
# 1. Unicode bullets → Standard markdown
"• Point" → "- Point"

# 2. Colons in headings
"**Overview:**" → "**Overview**"
"**Title :**" → "**Title**"

# 3. Proper spacing
"**Heading**\nText" → "**Heading**\n\nText"
"text\n- item" → "text\n\n- item"

# 4. Excessive whitespace
"text\n\n\n\nmore" → "text\n\nmore"
"word    word" → "word word"
```

#### ❌ DON'T Clean These:

```python
# Valid markdown that should NOT be modified:
- Colons in sentences: "The result: success"
- Bold within text: "This is **important** text"
- Inline formatting: "`code here`"
- Natural punctuation
- List content structure
```

### Code Locations

#### 1. AI Prompt Configuration
**File**: `chat/services.py`  
**Functions**: `generate_response()`, `generate_response_stream()`  
**Lines**: 495-539, 634-678

```python
system_prompt = """You are a professional knowledge base assistant.

FORMATTING GUIDELINES:
- Use **bold text** for section headings (1-3 words, no colons)
- Add blank line after each heading
- Use hyphens (-) for bullet points
- Add blank lines before and after lists
"""
```

#### 2. Backend Markdown Cleaning
**File**: `chat/templatetags/markdown_extras.py`  
**Function**: `_clean_markdown_text()`  
**Lines**: 45-71

```python
def _clean_markdown_text(text):
    """Minimal cleaning - only fix truly problematic patterns"""
    # 1. Unicode bullets → hyphens
    # 2. Colons in headings only
    # 3. Proper spacing
    # 4. Excessive whitespace
    return text.strip()
```

#### 3. Frontend Markdown Cleaning
**File**: `knowledgeassistant/templates/chatbot/chat.html`  
**Function**: `cleanTextFormatting()`  
**Lines**: 1342-1368

```javascript
cleanTextFormatting(text) {
    // Matches backend _clean_markdown_text exactly
    // 1. Unicode bullets → hyphens
    // 2. Colons in headings only
    // 3. Proper spacing
    // 4. Excessive whitespace
    return text.trim();
}
```

#### 4. Database Storage
**File**: `chat/views.py`  
**Functions**: `send_message()`, `send_message_stream()`  
**Lines**: 268-272, 338-342

```python
# Save ORIGINAL markdown to database
assistant_message = ChatMessage.objects.create(
    session=session,
    message_type='assistant',
    content=response_content  # Original markdown preserved
)
```

### Common Markdown Patterns

#### Headers
```markdown
**Section Title**

Content here.
```

#### Bullet Lists
```markdown
**Key Points**

- First point
- Second point
- Third point
```

#### Mixed Content
```markdown
**Overview**

This is a paragraph with important information.

**Details**

- Point one with details
- Point two with details

**Conclusion**

Final paragraph wrapping up the topic.
```

### Troubleshooting

#### Problem: Formatting lost after refresh
**Solution**: Check that `markdownify` filter is being used in template:
```django
{{ message.content|markdownify }}
```

#### Problem: Headings show colons
**Solution**: Verify cleaning functions are applied in both:
- `markdown_extras.py` (backend)
- `chat.html` cleanTextFormatting() (frontend)

#### Problem: No bullet points rendering
**Solution**: Check for proper spacing before lists:
```markdown
text

- item  ← blank line before list
```

#### Problem: Streaming vs non-streaming different
**Solution**: Both should use same cleaning and rendering:
- Streaming: `cleanTextFormatting()` + `formatMessage()`
- Page load: `_clean_markdown_text()` + markdown library

### Testing Checklist

- [ ] AI generates proper markdown (check prompt)
- [ ] Markdown saved to DB correctly (check content field)
- [ ] Streaming renders correctly (check JavaScript)
- [ ] Page load renders correctly (check template filter)
- [ ] Refresh preserves formatting (check full cycle)
- [ ] Headings appear bold without colons
- [ ] Lists appear as bullet points
- [ ] Paragraphs have proper spacing

### Best Practices

1. **Never modify markdown in database** - Keep it pure
2. **Clean at render time** - Not at storage time
3. **Match cleaning logic** - Backend and frontend identical
4. **Test both paths** - Streaming and page load
5. **Verify persistence** - Always test after refresh

### Dependencies

- **Backend**: Python `markdown` library with extensions
  ```python
  extensions=['extra', 'nl2br', 'sane_lists']
  ```

- **Frontend**: Marked.js v9.1.6
  ```javascript
  marked.setOptions({breaks: false, gfm: true})
  ```

### Quick Debugging

```python
# Check what's in database
message = ChatMessage.objects.last()
print(repr(message.content))  # Should show raw markdown with \n

# Check what AI produces
response = chat_service.generate_response(messages, chunks)
print(repr(response))  # Should show proper markdown

# Check what gets rendered
from chat.templatetags.markdown_extras import markdownify
html = markdownify(message.content)
print(html)  # Should show proper HTML
```

---

**Version**: 1.0  
**Last Updated**: 2025-10-08  
**Maintained By**: Development Team

