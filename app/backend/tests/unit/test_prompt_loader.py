"""Unit tests for PromptLoader."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from research_agent.infrastructure.llm.prompts import (
    PromptLoader,
    PromptLoaderError,
)


class TestPromptLoader:
    """Test cases for PromptLoader class."""

    def test_init_with_default_templates_dir(self):
        """Test initialization with default templates directory."""
        loader = PromptLoader()
        assert loader.templates_dir.exists()
        assert loader.templates_dir.name == "templates"

    def test_init_with_custom_templates_dir(self):
        """Test initialization with custom templates directory."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            loader = PromptLoader(templates_dir=tmppath)
            assert loader.templates_dir == tmppath

    def test_init_with_nonexistent_dir(self):
        """Test initialization fails with non-existent directory."""
        with pytest.raises(PromptLoaderError, match="Templates directory not found"):
            PromptLoader(templates_dir=Path("/nonexistent/templates"))

    def test_render_existing_template(self):
        """Test rendering an existing template."""
        loader = PromptLoader()
        # Test rendering the RAG system template
        result = loader.render("rag/system.j2")
        assert "research assistant" in result.lower()
        assert "documents" in result.lower()

    def test_render_template_with_variables(self):
        """Test rendering a template with variable substitution."""
        loader = PromptLoader()
        result = loader.render(
            "agents/summary/generation.j2",
            title="Test Document",
            content="This is test content.",
        )
        assert "Test Document" in result
        assert "This is test content" in result

    def test_render_nonexistent_template(self):
        """Test rendering a non-existent template raises error."""
        loader = PromptLoader()
        with pytest.raises(PromptLoaderError, match="Template not found"):
            loader.render("nonexistent/template.j2")

    def test_render_memory_aware_system_prompt(self):
        """Test rendering RAG system prompt with memory_aware flag."""
        loader = PromptLoader()
        # Without memory_aware
        result_basic = loader.render("rag/system.j2")
        assert "Conversation Summary" not in result_basic

        # With memory_aware
        result_memory = loader.render("rag/system.j2", memory_aware=True)
        assert "Conversation Summary" in result_memory
        assert "Build on previous context" in result_memory

    def test_get_template(self):
        """Test getting a template object directly."""
        loader = PromptLoader()
        template = loader.get_template("rag/system.j2")
        assert template is not None
        # Template can be rendered
        result = template.render()
        assert "research assistant" in result.lower()

    def test_get_template_nonexistent(self):
        """Test getting a non-existent template raises error."""
        loader = PromptLoader()
        with pytest.raises(PromptLoaderError, match="Template not found"):
            loader.get_template("nonexistent/template.j2")

    def test_list_templates(self):
        """Test listing all templates."""
        loader = PromptLoader()
        templates = loader.list_templates()
        assert len(templates) > 0
        # Should include our proof-of-concept templates
        assert "rag/system.j2" in templates
        assert "synthesis/reasoning.j2" in templates

    def test_validate_templates(self):
        """Test template validation."""
        loader = PromptLoader()
        validated = loader.validate_templates()
        assert len(validated) > 0
        # All templates should be valid
        assert "rag/system.j2" in validated

    def test_singleton_instance(self):
        """Test singleton pattern."""
        PromptLoader.reset_instance()
        loader1 = PromptLoader.get_instance()
        loader2 = PromptLoader.get_instance()
        assert loader1 is loader2

    def test_reset_instance(self):
        """Test resetting singleton instance."""
        PromptLoader.reset_instance()
        loader1 = PromptLoader.get_instance()
        PromptLoader.reset_instance()
        loader2 = PromptLoader.get_instance()
        assert loader1 is not loader2


class TestSynthesisReasoningTemplate:
    """Test cases for synthesis reasoning template."""

    def test_reasoning_template_renders(self):
        """Test that reasoning template renders correctly."""
        loader = PromptLoader()
        result = loader.render(
            "synthesis/reasoning.j2",
            inputs="--- INPUT 1 ---\nFirst input\n\n--- INPUT 2 ---\nSecond input",
        )
        assert "Domain Analysis" in result
        assert "Potential Bridges" in result
        assert "First input" in result
        assert "Second input" in result


class TestSummaryTemplates:
    """Test cases for summary templates."""

    def test_summary_system_template_renders(self):
        """Test that summary system template renders correctly."""
        loader = PromptLoader()
        result = loader.render("agents/summary/system.j2")
        assert "executive summaries" in result.lower()
        assert "JSON" in result

    def test_summary_generation_template_renders(self):
        """Test that summary generation template renders correctly."""
        loader = PromptLoader()
        result = loader.render(
            "agents/summary/generation.j2",
            title="Research Paper",
            content="This is the content of the research paper about AI.",
        )
        assert "Research Paper" in result
        assert "content of the research paper" in result
        assert "keyFindings" in result
