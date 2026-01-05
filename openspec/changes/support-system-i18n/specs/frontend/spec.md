## ADDED Requirements
### Requirement: Internationalization
The frontend SHALL support switching the interface language at runtime.

#### Scenario: Language switching
- **WHEN** the user selects a different language (e.g., "Chinese") from the language switcher
- **THEN** the UI text SHALL update to the selected language immediately or after reload
- **AND** the preference SHALL be persisted (e.g., via cookie)

#### Scenario: Default language
- **WHEN** the user visits the site for the first time
- **THEN** the system SHALL attempt to detect the browser language
- **AND** default to English if the detected language is not supported
