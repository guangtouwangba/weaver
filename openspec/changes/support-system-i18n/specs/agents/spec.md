## ADDED Requirements
### Requirement: Multilingual Output
Agents SHALL invoke LLMs with explicit instructions to generate output in the requested language.

#### Scenario: Summary in target language
- **WHEN** a summary is requested with `language="zh"`
- **THEN** the `SummaryAgent` SHALL generate the executive summary in Chinese
- **AND** key finding labels SHALL be in Chinese

#### Scenario: Mindmap in target language
- **WHEN** a mindmap is generated with `language="zh"`
- **THEN** the central topic and subtopics SHALL be in Chinese

#### Scenario: Flashcard in target language
- **WHEN** flashcards are generated with `language="zh"`
- **THEN** questions and answers SHALL be in Chinese

#### Scenario: Synthesis in target language
- **WHEN** synthesis is performed with `language="zh"`
- **THEN** the synthesized content SHALL be in Chinese
