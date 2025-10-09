# Final Response Format Guide

## Key Issues Fixed

### ❌ BAD Response Example:
```
Outreach

Use Outreach when:
- Information needs to be disseminated quickly.
- Unidirectional flow of information from Health Department
- Establishes communication channels

Pros:
- Quick, broad dissemination possible.

Cons:
- Limited public/community input or influence.

**Collaboration (Not explicitly mentioned in the context)**
```

**Problems:**
- Too mechanical with "Use when:", "Pros:", "Cons:"
- Says "(Not explicitly mentioned in the context)" - NEVER do this!
- Doesn't feel natural or conversational
- Sounds like a template, not a real explanation

### ✅ GOOD Response Example:
```
**Outreach**

Use outreach when you need to quickly disseminate public health information, such as during infectious disease outbreaks or emergency situations. Outreach works well when information flows primarily one direction and you want to establish communication channels or invite further engagement. It's less resource-intensive but offers limited community input opportunities.

**Collaboration**

Use collaboration when you're working on complex issues that benefit from community expertise, when you need sustained partnerships, and when you want community buy-in and ownership. Collaboration involves developing deeper relationships built on trust, with decisions made through consensus between the Health Department and external partners. This requires more commitment and resources over time but is more likely to achieve better public health outcomes.
```

**Why it's good:**
- Natural, flowing sentences
- **Bold headings** only for major topic separations
- Conversational and easy to read
- No mechanical structures like "Pros:" or "Use when:"
- No meta-commentary about the context

## Critical Rules

### 1. NEVER Mention Context/Sources
❌ BAD: "(Not explicitly mentioned in the context)"
❌ BAD: "(Document: NYC Community Engagement Framework)"
❌ BAD: "According to the document..."
❌ BAD: "The context mentions..."

✅ GOOD: Just provide the information directly

### 2. Write Naturally, Not Mechanically
❌ BAD: "Use Outreach when: - bullet - bullet - bullet"
❌ BAD: "Pros: - bullet Cons: - bullet"
❌ BAD: "Definition: Collaboration is..."

✅ GOOD: "Use outreach when you need to quickly disseminate..."
✅ GOOD: "Collaboration involves developing deeper relationships..."

### 3. Use Headings Strategically
✅ GOOD: Use **bold headings** to separate major topics (Outreach vs Collaboration)
❌ BAD: Don't use headings for every little section like "Pros", "Cons", "Use when"

### 4. Bullet Points - Use Sparingly
✅ GOOD: Use bullets for actual lists of 3+ distinct items
❌ BAD: Don't use bullets for every piece of information
❌ BAD: Don't structure entire responses as bullet lists

### 5. Be Conversational
✅ GOOD: Write complete, flowing sentences that connect ideas
❌ BAD: Don't write in fragments or telegraphic style

## Response Structure Examples

### Comparison Questions
```
**[Topic 1]**

[Natural paragraph explaining when/why/how to use it, 2-4 sentences]

**[Topic 2]**

[Natural paragraph explaining when/why/how to use it, 2-4 sentences]

[Optional closing sentence about how they relate]
```

### Simple Definition Questions
```
[Natural paragraph with 2-4 sentences explaining the concept]

[Optional second paragraph with additional context if needed]
```

### Multi-Part Explanation Questions
```
[Opening paragraph with main explanation]

**[Aspect 1]**

[Explanation in natural sentences]

**[Aspect 2]**

[Explanation in natural sentences]
```

## What Changed in the Code

### System Prompt Updates:
1. Added rule: "NEVER mention what's in or not in the context"
2. Added rule: "Write naturally - avoid mechanical structures like 'Use when:', 'Pros:', 'Cons:'"
3. Changed guidance: "Write in flowing, conversational prose"
4. Updated examples to show natural writing style

### User Message Updates:
- Changed from: "Provide a clear, well-structured answer"
- Changed to: "Provide a natural, well-written answer... Write conversationally, not in a mechanical template format"

## Testing Checklist

- [ ] Responses feel natural and conversational
- [ ] No mechanical structures ("Use when:", "Pros:", "Cons:")
- [ ] No meta-commentary about context or documents
- [ ] **Bold headings** only for major topic separations
- [ ] Flowing sentences, not bullet lists for everything
- [ ] Proper paragraphs with 2-4 connected sentences
- [ ] Information from knowledge base only
- [ ] No document citations in the response text

## Temperature Settings
- `temperature`: 0.1 (consistent responses)
- `num_predict`: 512 (allows detailed explanations)
- Natural writing style maintained even with low temperature

