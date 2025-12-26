## ADDED Requirements

### Requirement: Icon System
The frontend SHALL use `@mui/icons-material` as the single source for all icons, ensuring visual consistency with the MUI design system.

#### Scenario: Icon import and usage
- **WHEN** a component needs to display an icon
- **THEN** it SHALL import from `@mui/icons-material`
- **AND** the icon SHALL accept standard MUI `SvgIconProps`

#### Scenario: IconWrapper component
- **WHEN** a component uses `IconWrapper` for icon rendering
- **THEN** the wrapper SHALL accept MUI icon components
- **AND** SHALL pass through `SvgIconProps` for customization

#### Scenario: Icon sizing and theming
- **WHEN** an icon is rendered
- **THEN** it SHALL respect MUI theme colors
- **AND** SHALL support `fontSize` prop ('small', 'medium', 'large', or pixel values)
- **AND** SHALL support `color` prop for semantic coloring ('primary', 'secondary', 'error', etc.)

