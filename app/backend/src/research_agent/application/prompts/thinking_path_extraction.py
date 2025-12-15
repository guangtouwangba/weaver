"""Prompts for thinking path extraction.

This module extracts conversation structure to visualize the user's exploration journey:
- User questions become Question nodes
- AI responses become Answer nodes (summarized) + Insight nodes (key points)

Extended for Thinking Graph:
- Intent classification (continuation, branch, new_topic)
- Structured step extraction with claim, reason, evidence, uncertainty, decision
- Related concepts and suggested branches for mind map visualization
"""

# =============================================================================
# THINKING GRAPH PROMPTS (New - for dynamic mind map)
# =============================================================================

THINKING_GRAPH_INTENT_CLASSIFICATION_PROMPT = """
You are an expert at analyzing conversation flow and classifying user intent.

Given the conversation history and the current message, determine the INTENT type:

### Intent Types:
- **continuation**: The message directly follows up on the previous topic, asking for clarification, more details, or building on the last response.
- **branch**: The message explores a tangent or related aspect that was mentioned before, but not the immediate previous topic. It's a "fork" in the thinking path.
- **new_topic**: The message starts a completely unrelated discussion that doesn't connect to any previous context.

### Input:
- Conversation history (recent messages)
- Current message to classify
- List of active topics with their keywords

### Output Format (JSON only, no markdown):
{
  "intent": "continuation" | "branch" | "new_topic",
  "confidence": 0.0-1.0,
  "parent_topic_id": "ID of the topic this branches from (if branch), null otherwise",
  "reasoning": "Brief explanation of why this classification was chosen"
}
"""

THINKING_GRAPH_INTENT_USER_PROMPT = """
Classify the intent of the following message in the context of this conversation.

### Active Topics:
{active_topics}

### Recent Conversation:
{conversation_history}

### Current Message to Classify:
{current_message}

Output valid JSON only.
"""

THINKING_GRAPH_EXTRACTION_SYSTEM_PROMPT = """
You are an expert at analyzing conversations and building thinking graphs (mind maps).

Analyze the chat message and AI response to extract a structured "thinking step" that can be visualized as a node in a mind map.

### Output Format (JSON only, no markdown):
{
  "step": {
    "claim": "The main point, question, or assertion (1 sentence, max 100 chars)",
    "reason": "Why this point matters or why it's being explored (1 sentence)",
    "evidence": "Supporting information, data, or examples mentioned",
    "uncertainty": "What's still unclear, limitations, or caveats",
    "decision": "Conclusion, action item, or next step (if any)"
  },
  "related_concepts": ["concept1", "concept2", "concept3"],
  "suggested_branches": [
    {
      "type": "question",
      "content": "A follow-up question the user might want to explore"
    },
    {
      "type": "alternative", 
      "content": "An alternative perspective or approach"
    },
    {
      "type": "counterargument",
      "content": "A potential counterpoint or limitation"
    }
  ],
  "keywords": ["keyword1", "keyword2", "keyword3"]
}

### Rules:
1. `claim` should be concise - it will be the main node label (max 100 characters)
2. `reason`, `evidence`, `uncertainty`, `decision` can be empty strings if not applicable
3. Extract 1-5 `related_concepts` - nouns or noun phrases that are key topics
4. Suggest 1-3 `branches` that represent natural follow-up paths
5. Extract 3-5 `keywords` for semantic matching and duplicate detection
6. Focus on the SUBSTANCE of the exchange, not meta-commentary
7. Output valid JSON ONLY - no markdown fencing, no explanations
"""

THINKING_GRAPH_EXTRACTION_USER_PROMPT = """
Extract a thinking step from this exchange:

### User Message:
{user_message}

### AI Response:
{ai_response}

### Context (previous topic, if any):
{context}

Output valid JSON only.
"""

# =============================================================================
# ORIGINAL PROMPTS (Legacy - for linear extraction)
# =============================================================================

THINKING_PATH_EXTRACTION_SYSTEM_PROMPT = """
You are an expert at summarizing Q&A exchanges and extracting key insights.

Your task is to analyze a user question and AI response, then extract:
1. A short title (3-6 words) that captures the topic
2. A concise summary that directly answers the user's question (1-2 sentences)
3. Key insights or takeaways from the response (2-4 bullet points)

This will be used to build a visual "Thinking Path" that shows the user's exploration journey.

### Output Format
Return a valid JSON object with `title`, `summary` and `insights`.

```json
{
  "title": "外汇超短线交易指南",
  "summary": "A 1-2 sentence summary directly answering the user's question.",
  "insights": [
    {
      "id": "i1",
      "title": "Short Title (3-6 words)",
      "content": "A brief explanation of this key point (1-2 sentences)."
    }
  ]
}
```

### Critical Rules
1. **title** MUST be SHORT (3-6 words / 10-20 Chinese characters max). It should capture the topic, not repeat the question.
   - Good: "外汇超短线交易概述", "双十字星突破定义", "箱体突破策略"
   - Bad: "这本书讲了外汇超短线交易的多个方面" (too long)
2. **summary** MUST directly answer the user's question using terminology from the ORIGINAL question.
3. **DO NOT** invent or substitute words that aren't in the original content. 
   - If user asks about "article/文章", do NOT say "code/代码"
   - If user asks about "双十字星突破", use exactly that term, not a paraphrase
4. **summary** should be self-contained and understandable without reading the full response.
5. Extract 2-4 **insights** - the most important takeaways. For short answers, 1-2 insights is fine.
6. Each insight **title** should be SHORT (3-6 words max) - this will be displayed as a node label.
7. Each insight **content** should be a brief explanation (1-2 sentences max).
8. If the AI response is very short (1-2 sentences), you can use it directly as the summary.
9. STRICTLY output valid JSON only. No markdown fencing.
"""

THINKING_PATH_EXTRACTION_USER_PROMPT = """
Analyze this Q&A exchange and extract a summary that answers the question, plus key insights.

### User's Original Question (use this terminology in your summary):
{question}

### AI's Response:
{response}

Remember: Your summary must use the same terminology as the user's question. Do not substitute words.
Output valid JSON only.
"""
