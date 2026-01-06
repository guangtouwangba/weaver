# design-system Specification

## Purpose
TBD - created by archiving change refactor-design-system. Update Purpose after archive.
## Requirements
### Requirement: Design Token System
The frontend SHALL have a centralized token system for colors, spacing, typography, shadows, and radii.

#### Scenario: Using color tokens
- **GIVEN** a developer needs a primary color
- **WHEN** they import from `@/components/ui/tokens`
- **THEN** they receive a semantic value (e.g., `colors.primary[500]`)
- **AND** the value is consistent across all components

#### Scenario: Token sync with Tailwind
- **GIVEN** tokens are defined in TypeScript
- **WHEN** Tailwind CSS v4 is configured
- **THEN** tokens MAY be synced via CSS custom properties or `@theme`

---

### Requirement: Core UI Primitives
The frontend SHALL provide abstraction components (`Stack`, `Text`, `Button`, `IconButton`, `Surface`, `Tooltip`, `Spinner`, `Collapse`, `Skeleton`) that wrap the underlying UI library.

#### Scenario: Using Stack for layout
- **GIVEN** a developer needs a flex container
- **WHEN** they use `<Stack direction="row" gap={4}>`
- **THEN** it renders a flex container with appropriate gap
- **AND** does not require direct MUI import

#### Scenario: Using Text for typography
- **GIVEN** a developer needs styled text
- **WHEN** they use `<Text variant="h1" color="primary">`
- **THEN** it applies token-based typography and color
- **AND** renders semantic HTML (e.g., `<h1>`)

---

### Requirement: Composite Components
The frontend SHALL provide higher-level components (`Card`, `Dialog`, `Menu`, `Input`) built from primitives.

#### Scenario: Using Card
- **GIVEN** a developer needs a card container
- **WHEN** they use `<Card header="Title">Content</Card>`
- **THEN** it renders a `Surface` with header and body sections
- **AND** styling follows design tokens

---

### Requirement: Icon Independence
The icon abstraction layer SHALL NOT require MUI's `SvgIcon` in its final form.

#### Scenario: Rendering an icon
- **GIVEN** a developer imports `AddIcon` from `@/components/ui/icons`
- **WHEN** the icon is rendered
- **THEN** it uses pure SVG or a headless icon source
- **AND** MUI is not a transitive dependency for icons

