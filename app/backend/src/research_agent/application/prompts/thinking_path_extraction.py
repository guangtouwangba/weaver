"""Prompts for thinking path extraction.

This module extracts conversation structure to visualize the user's exploration journey:
- User questions become Question nodes
- AI responses become Answer nodes (summarized) + Insight nodes (key points)
"""

THINKING_PATH_EXTRACTION_SYSTEM_PROMPT = """
You are an expert at summarizing AI responses and extracting key insights.

Your task is to analyze an AI response and extract:
1. A concise summary of the answer (1-2 sentences)
2. Key insights or takeaways from the response (3-5 bullet points)

This will be used to build a visual "Thinking Path" that shows the user's exploration journey through their conversation.

### Output Format
Return a valid JSON object with `summary` and `insights`.

```json
{
  "summary": "A 1-2 sentence summary of the AI's answer.",
  "insights": [
    {
      "id": "i1",
      "title": "Short Title (3-6 words)",
      "content": "A brief explanation of this key point (1-2 sentences)."
    },
    {
      "id": "i2", 
      "title": "Another Key Point",
      "content": "Explanation of this insight."
    }
  ]
}
```

### Rules
1. The `summary` should capture the essence of the AI's answer in 1-2 sentences.
2. Extract 3-5 `insights` - the most important takeaways from the response.
3. Each insight `title` should be SHORT (3-6 words max) - this will be displayed as a node label.
4. Each insight `content` should be a brief explanation (1-2 sentences max).
5. Focus on WHAT the AI said, not HOW it reasoned.
6. If the response is very short or simple, you can return fewer insights (minimum 1).
7. STRICTLY output valid JSON only. No markdown fencing.
"""

THINKING_PATH_EXTRACTION_USER_PROMPT = """
Analyze the following AI response and extract a summary and key insights.

User Question: {question}

AI Response:
{response}
"""
