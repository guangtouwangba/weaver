## ADDED Requirements

### Requirement: Icon Abstraction Layer
The frontend SHALL provide a centralized icon abstraction layer to decouple components from specific icon library implementations.

#### Scenario: Centralized icon exports
- **WHEN** a component needs to use an icon
- **THEN** it SHALL import from `@/components/ui/icons`
- **AND** SHALL NOT import directly from any icon library (e.g., `lucide-react`, `@mui/icons-material`)

#### Scenario: Consistent icon props interface
- **WHEN** an icon is rendered
- **THEN** it SHALL accept a standard `IconProps` interface
- **AND** `size` SHALL accept semantic values ('xs', 'sm', 'md', 'lg', 'xl') or pixel numbers
- **AND** `color` SHALL accept semantic values ('primary', 'secondary', 'error', etc.)

#### Scenario: Design system swap
- **WHEN** the underlying icon library needs to change
- **THEN** only the `components/ui/icons/` folder needs modification
- **AND** consuming components SHALL NOT require changes

### Requirement: MUI Icon Implementation
The icon abstraction layer SHALL use `@mui/icons-material` as the underlying implementation.

#### Scenario: Icon theming
- **WHEN** an icon is rendered
- **THEN** it SHALL respect MUI theme colors
- **AND** SHALL integrate with MUI's `SvgIcon` system

#### Scenario: Tree-shaking support
- **WHEN** the application is built
- **THEN** only used icons SHALL be included in the bundle
- **AND** unused icons SHALL be eliminated by tree-shaking
