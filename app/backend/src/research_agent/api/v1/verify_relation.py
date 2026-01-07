"""Verify relation API endpoints."""

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from research_agent.api.deps import get_llm_service
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.shared.utils.logger import logger

router = APIRouter()


class VerifyRelationRequest(BaseModel):
    """Request model for relation verification."""

    source_content: str
    target_content: str
    relation_type: str  # 'support', 'contradict', 'correlates'


class VerifyRelationResponse(BaseModel):
    """Response model for relation verification."""

    valid: bool
    reasoning: str
    confidence: float


VERIFY_RELATION_PROMPT = """You are an expert logic analyzer.
Verify if the claimed relationship between two pieces of content is valid.

Source: "{source}"
Target: "{target}"
Claimed Relationship: "{relation}"

Analyze the logical connection.
- Support: Does Source provide evidence/reasoning for Target?
- Contradict: Does Source refute/oppose Target?
- Correlates: Is there a strong thematic connection?

Respond with JSON only:
{{
  "valid": boolean,
  "reasoning": "string (concise explanation)",
  "confidence": float (0.0 to 1.0)
}}
"""


@router.post("/canvas/verify-relation", response_model=VerifyRelationResponse)
async def verify_relation(
    request: VerifyRelationRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> VerifyRelationResponse:
    """Verify a logical relationship between two content pieces."""
    prompt = VERIFY_RELATION_PROMPT.format(
        source=request.source_content,
        target=request.target_content,
        relation=request.relation_type,
    )

    messages = [
        ChatMessage(role="system", content="You are a logic validation engine. Output JSON only."),
        ChatMessage(role="user", content=prompt),
    ]

    try:
        response = await llm_service.chat(messages)
        content = response.content.strip()
        # strip markdown code blocks if any
        if content.startswith("```"):
            first_newline = content.find("\n")
            if first_newline != -1:
                content = content[first_newline + 1 :]
            if content.endswith("```"):
                content = content[:-3].strip()
            elif "```" in content:
                content = content[: content.rfind("```")].strip()

        data = json.loads(content)
        return VerifyRelationResponse(**data)
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return VerifyRelationResponse(
            valid=False, reasoning=f"AI verification failed: {str(e)}", confidence=0.0
        )
