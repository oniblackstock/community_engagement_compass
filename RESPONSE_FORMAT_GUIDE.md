# Response Format Guide

## Overview
The chatbot now provides direct, well-structured answers using multiple paragraphs instead of rigid Q&A format or excessive bullet points.

## Key Principles

### 1. **Direct Answers**
- Start immediately with the answer
- No "Q:" or "A:" labels
- No question repetition
- No preambles like "According to the document..."
- **NEVER mention document names or citations** (e.g., "Document: NYC Framework")

### 2. **Strategic Use of Headings and Bullets**
- Use **bold headings** to separate major sections
- Use bullet points for lists of features, characteristics, or key points
- Use paragraphs for explanations and context
- Blank lines between sections for readability

### 3. **Precise and Non-Repetitive**
- Avoid stating the same information multiple times
- Each point should be clear and concise
- No redundant explanations

### 4. **Appropriate Length**
- Simple questions: 1-2 paragraphs (2-6 sentences)
- Complex questions: Multiple sections with headings (up to 512 tokens)
- Comparisons: Use headings for each item with bullet points for characteristics
- Lists: Use bullet points, not repetitive prose

## Example Responses

### Example 1: Comparison Question with Headings and Bullets
**Question:** "When should I use outreach versus collaboration?"

**Response:**
```
**Outreach**

Use outreach when you need quick, broad dissemination of public health information, such as during infectious disease outbreaks or emergencies. Key characteristics:

- Unidirectional information flow from Health Department to communities
- Establishes communication channels for future engagement
- Less resource-intensive approach
- Can stimulate further discussion and involvement

**Collaboration**

Use collaboration for complex issues requiring deeper stakeholder relationships and shared decision-making. Key characteristics:

- Bidirectional communication and consensus-building
- Shared leadership with stakeholders working toward common goals
- More time and resource commitment required
- Likely to achieve better long-term public health outcomes

Outreach can evolve into collaboration over time as relationships develop.
```

### Example 2: Simple Definition (No document citations)
**Question:** "What is consultation?"

**Response:**
```
Consultation is an information-seeking practice where the Health Department shares proposals with communities and solicits their feedback, which then influences agency decisions. The Health Department still makes final decisions but considers community input. Communication flows to the community and back.
```

**NOTE:** No mention of "(Document: NYC Community Engagement Framework)" or any other source citations in the response.

### Example 3: Definition/Concept Question
**Question:** "What does 'shared leadership' mean in practice?"

**Response:**
```
Shared leadership means creating a strong system of relationships, reciprocity, and trust where stakeholders are represented equally in the partnership. It involves consensus-driven decision-making, shared planning and accountability, shared responsibility for outcomes, and participatory evaluation.

The Health Department shares control with communities and remains flexible about how the group identifies problems and develops solutions. This leads to collective ownership of both the problem and its solution, with increased responsibility, accountability, power, and diversity of strategies. It acknowledges that the Health Department is not the only expert for a given project.
```

### Example 4: Specific Example Question
**Question:** "Can you give me an example of when outreach would be the right choice?"

**Response:**
```
During an infectious disease outbreak, the Health Department might strategically conduct a vigorous outreach campaign to inform communities most likely to be affected by the outbreak, as well as medical providers who serve those communities. In this emergency situation, the flow of information is almost entirely unidirectional and the priority is rapid, broad dissemination of critical public health information.
```

## Formatting Rules

### DO:
✅ Start directly with the answer
✅ Use **bold headings** to separate major sections
✅ Use bullet points for lists of characteristics, features, or key points
✅ Use paragraphs for explanations and context
✅ Add blank lines between sections
✅ Keep responses precise and non-repetitive
✅ Provide complete explanations with appropriate detail

### DON'T:
❌ Repeat the question back ("Q: What is...")
❌ Use Q&A labels
❌ Mention document names or citations like "(Document: NYC Framework)"
❌ Add unnecessary preambles like "According to the document..."
❌ Repeat the same information multiple times
❌ Use repetitive prose when bullets would be clearer
❌ Over-use or under-use formatting - be strategic

## Technical Implementation

### Model Parameters:
- `num_predict`: 512 tokens (allows multiple paragraphs)
- `temperature`: 0.1 (consistent, focused responses)
- `repeat_penalty`: 1.2 (avoid repetition)

### System Prompt Key Elements:
1. "Do NOT repeat the question back to the user"
2. "Use multiple paragraphs to organize different aspects"
3. "Use full sentences and explanatory paragraphs instead of bullet points"
4. "For comparisons, use separate paragraphs for each item"
5. Examples showing proper multi-paragraph structure

### Post-Processing:
- `post_process_response()` function ensures proper line breaks
- Blank lines maintained between paragraphs
- Formatting applied consistently in both streaming and non-streaming modes

## Response Length Guidelines

| Question Type | Typical Length | Paragraph Count |
|--------------|----------------|-----------------|
| Simple definition | 2-4 sentences | 1 paragraph |
| Comparison | 4-8 sentences | 2 paragraphs |
| Complex explanation | 6-12 sentences | 2-3 paragraphs |
| Multi-part question | 6-12 sentences | 2-4 paragraphs |
| Example scenario | 3-6 sentences | 1-2 paragraphs |

## Testing Checklist

- [ ] No question repetition in responses
- [ ] Responses use multiple paragraphs when appropriate
- [ ] No Q: or A: labels appear
- [ ] Blank lines between paragraphs
- [ ] Comparisons have separate paragraphs
- [ ] Explanatory prose instead of bullet lists
- [ ] Proper formatting in both streaming and non-streaming
- [ ] Appropriate length for question complexity

