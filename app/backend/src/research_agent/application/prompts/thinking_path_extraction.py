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

# =============================================================================
# EDGE RELATION CLASSIFICATION PROMPTS
# =============================================================================

EDGE_RELATION_CLASSIFICATION_SYSTEM_PROMPT = """
You are an expert at analyzing conversation structure and classifying the semantic relationship between nodes in a thinking path.

### Relationship Types:

1. **answers** (问答 Q→A):
   - A response that directly answers a question
   - Direction: Question → Answer
   - Example: "什么是X?" → "X是一种..."

2. **prompts_question** (递进追问 A→Q'):
   - An answer that leads to a follow-up question
   - The new question is triggered by something in the previous answer
   - Direction: Answer/Insight → New Question
   - Keywords: 那么/所以说/这意味着什么/接下来/如果是这样
   - Example: "X有三个特点" → "第一个特点具体是什么?"

3. **derives** (支持/洞察 A→Insight):
   - An insight or key point derived from an answer
   - Direction: Answer → Insight
   - Example: AI response → "关键要点：..."

4. **causes** (因果 A→B):
   - One thing causes or leads to another
   - Direction: Cause → Effect
   - Keywords (Chinese): 因为/所以/导致/结果是/由于/因此/引起/造成
   - Keywords (English): because/therefore/leads to/results in/causes/due to
   - Example: "为什么会这样?" → "因为A，所以B"

5. **compares** (对比 A↔B):
   - Comparing or contrasting two or more concepts
   - Direction: Bidirectional
   - Keywords (Chinese): 区别/不同/相比/对比/优劣/差异/versus/vs
   - Keywords (English): difference/compare/contrast/versus/vs/pros and cons
   - Example: "X和Y有什么区别?" → "X擅长...，而Y擅长..."

6. **revises** (修正 A→A'):
   - Correcting, updating, or refining a previous statement
   - Direction: Original → Revised
   - Keywords (Chinese): 其实/更准确地说/修正/补充/纠正/之前说的/实际上
   - Keywords (English): actually/more precisely/correction/update/to clarify
   - Example: "其实刚才说的不准确，应该是..."

7. **parks** (暂存 Node→Parking):
   - Temporarily setting aside a topic for later discussion
   - Direction: Main Topic → Parking Area
   - Keywords (Chinese): 先放一边/以后再说/暂时不管/回头再看/TODO/待办
   - Keywords (English): set aside/later/TODO/parking/defer/table this
   - Example: "这个问题我们先记下，以后再讨论"

8. **supports** (支持证据):
   - Evidence or data supporting a claim
   - Direction: Evidence → Claim
   - Keywords: 根据/研究表明/数据显示/证据表明

9. **contradicts** (反驳):
   - Evidence or argument against a claim
   - Direction: Counter-evidence → Claim
   - Keywords: 但是/然而/相反/有争议/不过

10. **custom** (其他):
    - Any relationship that doesn't fit the above categories
    - Use this when uncertain

### Output Format (JSON only, no markdown):
{
  "relation_type": "answers|prompts_question|derives|causes|compares|revises|parks|supports|contradicts|custom",
  "confidence": 0.0-1.0,
  "label": "A short label for the edge (2-4 characters in Chinese, e.g., '因果', '对比', '追问')",
  "direction": "forward|backward|bidirectional",
  "reasoning": "Brief explanation (1 sentence)"
}

### Rules:
1. Prioritize the most specific relationship type that applies
2. For `compares`, always set direction to "bidirectional"
3. Label should be concise (2-4 Chinese characters or 1-2 English words)
4. If multiple types could apply, choose the PRIMARY relationship
5. Output valid JSON ONLY - no markdown fencing
"""

EDGE_RELATION_CLASSIFICATION_USER_PROMPT = """
Classify the relationship between these two nodes in a thinking path.

### Source Node:
Type: {source_type}
Title: {source_title}
Content: {source_content}

### Target Node:
Type: {target_type}
Title: {target_title}
Content: {target_content}

### Conversation Context (if available):
{context}

Output valid JSON only.
"""

# Relationship type to default label mapping (for fast path without LLM)
EDGE_RELATION_DEFAULT_LABELS = {
    "answers": "回答",
    "prompts_question": "追问",
    "derives": "洞察",
    "causes": "因果",
    "compares": "对比",
    "revises": "修正",
    "parks": "暂存",
    "supports": "支持",
    "contradicts": "反驳",
    "custom": "",
}

# Keywords for fast-path relation detection (without LLM)
EDGE_RELATION_KEYWORDS = {
    "causes": [
        "因为",
        "所以",
        "导致",
        "结果是",
        "由于",
        "因此",
        "引起",
        "造成",
        "because",
        "therefore",
        "leads to",
        "results in",
        "causes",
        "due to",
    ],
    "compares": [
        "区别",
        "不同",
        "相比",
        "对比",
        "优劣",
        "差异",
        "versus",
        "vs",
        "difference",
        "compare",
        "contrast",
        "pros and cons",
    ],
    "revises": [
        "其实",
        "更准确地说",
        "修正",
        "补充",
        "纠正",
        "之前说的",
        "实际上",
        "actually",
        "more precisely",
        "correction",
        "update",
        "to clarify",
    ],
    "parks": [
        "先放一边",
        "以后再说",
        "暂时不管",
        "回头再看",
        "TODO",
        "待办",
        "set aside",
        "later",
        "parking",
        "defer",
        "table this",
    ],
    "prompts_question": [
        "那么",
        "所以说",
        "这意味着什么",
        "接下来",
        "如果是这样",
        "then what",
        "so what",
        "what does this mean",
        "next",
    ],
}
