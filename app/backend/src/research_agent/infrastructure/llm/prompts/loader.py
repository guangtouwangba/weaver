"""Jinja2 template loader for prompts.

This module provides a unified way to load and render prompt templates
stored as Jinja2 files, enabling:
- Separation of prompts from Python code
- Template inheritance and includes
- Easy testing and validation
- Future i18n support
"""

from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, Template, TemplateError, TemplateNotFound

from research_agent.shared.utils.logger import logger


class PromptLoaderError(Exception):
    """Exception raised for prompt loading/rendering errors."""

    pass


class PromptLoader:
    """
    Loads and renders Jinja2 prompt templates.

    Usage:
        loader = PromptLoader()
        prompt = loader.render("agents/summary/generation.j2", title="Doc", content="...")

    The loader looks for templates in the `templates/` directory relative to this file.
    Templates are cached for performance.
    """

    _instance: Optional["PromptLoader"] = None

    def __init__(self, templates_dir: Path | None = None):
        """
        Initialize the prompt loader.

        Args:
            templates_dir: Optional custom templates directory.
                          Defaults to ./templates/ relative to this file.
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"

        self._templates_dir = templates_dir

        if not templates_dir.exists():
            raise PromptLoaderError(f"Templates directory not found: {templates_dir}")

        # Configure Jinja2 environment
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            # Keep whitespace control minimal to preserve prompt formatting
            trim_blocks=True,
            lstrip_blocks=True,
            # Enable autoescape for safety (can be disabled per-template)
            autoescape=False,
            # Cache templates
            auto_reload=True,  # Set to False in production for better perf
        )

        logger.debug(f"[PromptLoader] Initialized with templates from: {templates_dir}")

    @classmethod
    def get_instance(cls) -> "PromptLoader":
        """Get or create a singleton instance of PromptLoader."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None

    def render(self, template_name: str, **variables: Any) -> str:
        """
        Render a template with the given variables.

        Args:
            template_name: Path to template relative to templates dir (e.g., "rag/system.j2")
            **variables: Template variables to substitute

        Returns:
            Rendered prompt string

        Raises:
            PromptLoaderError: If template not found or rendering fails
        """
        try:
            template = self._env.get_template(template_name)
            rendered = template.render(**variables)
            logger.debug(f"[PromptLoader] Rendered template: {template_name}")
            return rendered
        except TemplateNotFound:
            raise PromptLoaderError(f"Template not found: {template_name}")
        except TemplateError as e:
            raise PromptLoaderError(f"Error rendering template {template_name}: {e}")

    def get_template(self, template_name: str) -> Template:
        """
        Get a template object for more advanced usage.

        Args:
            template_name: Path to template relative to templates dir

        Returns:
            Jinja2 Template object

        Raises:
            PromptLoaderError: If template not found
        """
        try:
            return self._env.get_template(template_name)
        except TemplateNotFound:
            raise PromptLoaderError(f"Template not found: {template_name}")

    def validate_templates(self) -> list[str]:
        """
        Validate all templates in the templates directory.

        Returns:
            List of template paths that were validated

        Raises:
            PromptLoaderError: If any template fails to parse
        """
        validated = []
        errors = []

        for j2_file in self._templates_dir.rglob("*.j2"):
            relative_path = j2_file.relative_to(self._templates_dir)
            template_name = str(relative_path)

            try:
                # Try to load (parse) the template
                self._env.get_template(template_name)
                validated.append(template_name)
            except TemplateError as e:
                errors.append(f"{template_name}: {e}")

        if errors:
            error_msg = "Template validation errors:\n" + "\n".join(errors)
            raise PromptLoaderError(error_msg)

        logger.info(f"[PromptLoader] Validated {len(validated)} templates")
        return validated

    def list_templates(self) -> list[str]:
        """
        List all available template files.

        Returns:
            List of template paths relative to templates directory
        """
        templates = []
        for j2_file in self._templates_dir.rglob("*.j2"):
            relative_path = j2_file.relative_to(self._templates_dir)
            templates.append(str(relative_path))
        return sorted(templates)

    @property
    def templates_dir(self) -> Path:
        """Return the templates directory path."""
        return self._templates_dir


# Convenience function for simple usage
def render_prompt(template_name: str, **variables: Any) -> str:
    """
    Render a prompt template using the singleton loader.

    Args:
        template_name: Path to template (e.g., "rag/system.j2")
        **variables: Template variables

    Returns:
        Rendered prompt string
    """
    return PromptLoader.get_instance().render(template_name, **variables)
