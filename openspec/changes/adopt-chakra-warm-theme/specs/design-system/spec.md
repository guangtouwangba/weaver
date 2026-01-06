# Specification: Design System (Delta)

## MODIFIED Requirements

### Requirement: Color Token System
The design system SHALL provide a warm gray (Stone) palette as the neutral color scale, creating a paper-like reading experience suitable for knowledge management applications.

#### Scenario: Warm gray palette values
- **GIVEN** the application renders UI
- **WHEN** neutral colors are applied
- **THEN** gray.50 SHALL be `#FAFAF9` (canvas background)
- **AND** gray.100 SHALL be `#F5F5F4` (panel/sidebar)
- **AND** gray.200 SHALL be `#E7E5E4` (borders)
- **AND** gray.800 SHALL be `#292524` (primary text)
- **AND** all neutral grays SHALL have yellow/brown undertones

#### Scenario: Brand accent colors
- **GIVEN** the application needs primary action colors
- **WHEN** brand colors are applied
- **THEN** brand.500 SHALL be `#0D9488` (teal primary)
- **AND** brand.600 SHALL be `#0F766E` (hover state)

## ADDED Requirements

### Requirement: Chakra UI Integration
The frontend SHALL use Chakra UI as the component library foundation, configured with a custom warm theme while maintaining the existing primitives abstraction layer.

#### Scenario: Provider configuration
- **GIVEN** the application starts
- **WHEN** the root layout renders
- **THEN** ChakraProvider SHALL wrap all content
- **AND** the custom theme SHALL be applied

#### Scenario: Theme color overrides
- **GIVEN** Chakra UI is configured
- **WHEN** components use the `gray` color scheme
- **THEN** they SHALL render with warm gray values
- **AND** the default Chakra blue-gray SHALL NOT appear

#### Scenario: Primitives abstraction
- **GIVEN** feature code needs UI components
- **WHEN** importing components
- **THEN** imports SHALL be from `@/components/ui`
- **AND** imports SHALL NOT be directly from `@chakra-ui/react`

#### Scenario: Global body styles
- **GIVEN** the application loads
- **WHEN** the page renders
- **THEN** the body background SHALL be `gray.50`
- **AND** the body text color SHALL be `gray.800`

### Requirement: Component Decoupling
The design system SHALL maintain component abstraction to enable future design system swaps without requiring changes to feature code.

#### Scenario: Stable primitives API
- **GIVEN** a primitive component (Button, Text, Surface, etc.)
- **WHEN** the underlying implementation changes from CSS to Chakra
- **THEN** the component's prop interface SHALL remain unchanged
- **AND** feature code SHALL NOT require modifications
