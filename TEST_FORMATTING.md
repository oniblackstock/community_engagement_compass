# 🧪 Formatting Test Guide

## Quick Start Testing

### Step 1: Start the Server

```bash
cd /home/conovo-ai/Documents/knowledgeassistant
source venv/bin/activate
python manage.py runserver
```

### Step 2: Open Your Browser

Navigate to: `http://localhost:8000/chat/`

## Test Cases

### ✅ Test Case 1: Non-Streaming Response with Lists

**Action**: 
1. Disable streaming toggle
2. Ask: "What are the main community engagement strategies?"

**Expected Output**:
```
[Bold Heading] Community Engagement Strategies

[Paragraph explaining strategies]

[Bold Heading] Key Approaches

• Proper bullet point 1
• Proper bullet point 2
• Proper bullet point 3

[Paragraph with conclusion]
```

**Success Criteria**:
- ✓ Headings are bold and have proper spacing
- ✓ Bullet points appear as actual bullets, not hyphens or symbols
- ✓ Paragraphs have proper spacing
- ✓ No stray colons (`:`) after headings or in weird places

---

### ✅ Test Case 2: Streaming Response

**Action**:
1. Enable streaming toggle
2. Ask: "Explain the difference between outreach and engagement"

**Expected Output**:
- Text appears word-by-word
- Formatting applies correctly as text streams
- Final result has proper headings, lists, and paragraphs
- No formatting artifacts when streaming completes

**Success Criteria**:
- ✓ Streaming works smoothly
- ✓ Final formatting is clean and professional
- ✓ Headings and lists render correctly

---

### ✅ Test Case 3: Page Refresh Persistence (CRITICAL)

**Action**:
1. Send 2-3 messages with different formatting types
2. Press F5 or Ctrl+R to refresh the page
3. Observe all previous messages

**Expected Output**:
- All messages maintain their formatting
- Headings still bold
- Lists still formatted correctly
- No plain text or broken markdown

**Success Criteria**:
- ✓ Formatting persists after refresh
- ✓ No markdown symbols visible (`**`, `-`, etc.)
- ✓ Professional appearance maintained

---

### ✅ Test Case 4: Mixed Content

**Action**:
Ask: "What are community engagement strategies and how do they compare to traditional outreach?"

**Expected Output**:
```
[Bold Heading] Community Engagement Strategies

[Paragraph 1]

[Bold Heading] Traditional Outreach

[Paragraph 2]

[Bold Heading] Key Differences

• Difference 1
• Difference 2
• Difference 3

[Concluding paragraph]
```

**Success Criteria**:
- ✓ Multiple headings and sections work together
- ✓ Mixed paragraphs and lists render correctly
- ✓ Proper spacing throughout

---

## What to Look For

### ✅ GOOD Formatting
- **Bold headings** that stand out
- Proper bullet points (• or -) in `<ul>` lists
- Clean paragraph breaks
- Professional spacing
- No visible markdown syntax

### ❌ BAD Formatting (If you see this, report it)
- Plain text with `**Title**` visible
- Hyphens instead of bullets: `- item` shown literally
- Colons after headings: **Title:**
- Weird symbols: •, ·, ▪
- Compressed text with no spacing
- Markdown syntax visible after refresh

## Browser Console Checks

### Open Browser Console (F12)

Look for these messages:
```
✓ Enhanced chat interface initialized with streaming support
✓ Marked.js loaded
✓ Found X chat sessions
```

### Watch for Errors

If you see errors like:
- ❌ "Marked.js not loaded" → Marked.js failed to load
- ❌ "Error parsing markdown" → Formatting function failed

## Compare Before/After

### BEFORE the Fix
```
**Community Engagement:** Builds relationships.
**Outreach:** : Provides information.
- First point: involves dialogue
- Second point: requires resources
```

### AFTER the Fix
```
Community Engagement

Builds relationships through sustained interaction.

Outreach

Provides information to target populations.

Key Points
• Involves dialogue and feedback
• Requires resources and commitment
```

## Troubleshooting

### Issue: Formatting still broken after changes

**Solution**:
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+F5)
3. Restart Django server:
   ```bash
   # Press Ctrl+C in terminal
   python manage.py runserver
   ```

### Issue: Old messages still show bad formatting

**Explanation**: Old messages in database have old markdown, but they should be cleaned on display.

**Solution**: The `markdownify` filter will clean them automatically.

### Issue: Streaming shows raw markdown

**Solution**: Check browser console for JavaScript errors. Marked.js might not be loading.

## Success Checklist

After testing, you should be able to say YES to all:

- [ ] New messages show proper formatting (headings, lists, paragraphs)
- [ ] Streaming responses format correctly
- [ ] Page refresh maintains all formatting
- [ ] No markdown syntax visible in rendered messages
- [ ] No stray colons or bullet symbols
- [ ] Professional ChatGPT-like appearance
- [ ] Both streaming and non-streaming work identically

## Example Questions to Test

1. "What are community engagement best practices?"
2. "Compare and contrast outreach and engagement approaches"
3. "List the key principles of health equity communication"
4. "Explain the community engagement spectrum"
5. "What resources are available for community organizers?"

## Reporting Issues

If formatting still doesn't work:

1. **Take a screenshot** of the broken formatting
2. **Open browser console** (F12) and check for errors
3. **Note which test case** failed
4. **Check if it's streaming or non-streaming**
5. **Report**: "Test Case X failed - [describe issue]"

Example:
```
Test Case 3 failed - Page refresh shows raw markdown with ** symbols visible.
Browser: Chrome 120
Error in console: "Marked is not defined"
```

## Performance Notes

- Formatting should apply **instantly** for non-streaming
- Streaming should be **smooth** with no lag
- Page refresh should be **fast** (< 1 second)
- No memory leaks or slowdowns

---

## 🎉 Success Indicators

If all tests pass, you should see:
1. **Professional appearance** similar to ChatGPT
2. **Consistent formatting** across all messages
3. **Persistent formatting** after page refresh
4. **Clean markdown rendering** with no artifacts
5. **Happy users** who can read responses easily!

