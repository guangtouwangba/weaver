# prompts Specification

## ADDED Requirements

### Requirement: Prompt Template Loading
The system SHALL provide a centralized prompt loading mechanism using Jinja2 templates.

#### Scenario: Load and render a simple template
- **WHEN** a component requests a prompt template with variables
- **THEN** the system loads the corresponding `.j2` file
- **AND** renders it with the provided variables
- **AND** returns the complete prompt string

#### Scenario: Template includes shared partials
- **WHEN** a template uses `{% include '_base/guidelines.j2' %}`
- **THEN** the included partial is rendered inline
- **AND** the final prompt contains the shared content

#### Scenario: Template not found
- **WHEN** a component requests a non-existent template
- **THEN** the system raises a descriptive error
- **AND** logs the missing template path

### Requirement: Template Caching
The system SHALL cache compiled Jinja2 templates for performance.

#### Scenario: Repeated template rendering
- **WHEN** the same template is rendered multiple times
- **THEN** the compiled template is reused from cache
- **AND** only variable substitution is performed

### Requirement: Startup Validation
The system SHALL validate all prompt templates at application startup.

#### Scenario: Syntax error in template
- **WHEN** a template contains a Jinja2 syntax error
- **THEN** the application fails to start
- **AND** logs the specific error and template path

#### Scenario: Missing variable in template
- **WHEN** a template references a variable not in the rendering context
- **THEN** a clear error is raised at render time
- **AND** identifies the missing variable name

### Requirement: Template Organization
The system SHALL organize prompt templates in a hierarchical directory structure.

#### Scenario: Template discovery
- **WHEN** a developer looks for a prompt template
- **THEN** they can find it under `prompts/templates/` following the pattern:
  - `rag/*.j2` for RAG-related prompts
  - `agents/<agent_name>/*.j2` for agent-specific prompts
  - `synthesis/*.j2` for synthesis prompts
  - `_base/*.j2` for shared partials
