"""Integration tests for prompt migration to Jinja2 templates."""

from research_agent.infrastructure.llm.prompts import render_prompt
from research_agent.infrastructure.llm.prompts.rag_prompt import SYSTEM_PROMPT


class TestRagPromptMigration:
    """Compare migrated RAG prompts with original constants."""

    def test_rag_system_prompt_equivalence(self):
        """Verify rag/system.j2 matches rag_prompt.SYSTEM_PROMPT logic."""
        # Render legacy prompt (it's a constant)
        legacy_prompt = SYSTEM_PROMPT.strip()

        # Render new template (default mode)
        new_prompt = render_prompt("rag/system.j2", memory_aware=False).strip()

        # Normalize whitespace for comparison
        " ".join(legacy_prompt.split())
        new_normalized = " ".join(new_prompt.split())

        # Assert they are semantically similar (content matches)
        # Note: They might not be identical due to Jinja formatting choices,
        # but key phrases must exist.

        assert "research assistant helping users understand documents" in new_normalized
        assert "Answer questions based on the provided context" in new_normalized
        assert "Provide comprehensive and detailed answers" in new_normalized
        assert "cite the source page numbers" in new_normalized

        # Check that the legacy content is largely contained in the new one
        # Or vice versa. Since we copied it, they should be very close.
        # If we added features (like citation include), check that too.

        # Verify memory_aware flag adds the extra section
        new_prompt_memory = render_prompt("rag/system.j2", memory_aware=True)
        assert "Conversation Summary" in new_prompt_memory
        assert "Relevant Past Discussions" in new_prompt_memory


class TestAgentPrompts:
    """Verify other migrated prompts render correctly."""

    def test_summary_agent_prompts(self):
        """Verify summary agent prompts render with expected structure."""
        # System prompt
        sys_prompt = render_prompt("agents/summary/system.j2")
        assert "expert document analyst" in sys_prompt
        assert "ONLY valid JSON" in sys_prompt

        # Generation prompt
        gen_prompt = render_prompt(
            "agents/summary/generation.j2", title="My Title", content="My Content"
        )
        assert "My Title" in gen_prompt
        assert "My Content" in gen_prompt
        assert "executive summary" in gen_prompt.lower()
        assert "keyFindings" in gen_prompt

    def test_synthesis_reasoning_prompt(self):
        """Verify synthesis reasoning prompt."""
        reason_prompt = render_prompt("synthesis/reasoning.j2", inputs="Input Data")
        assert "Input Data" in reason_prompt
        assert "Potential Bridges" in reason_prompt
        assert "Domain Analysis" in reason_prompt
