# Design Tokens Specification

## MODIFIED Requirements

### Requirement: Primary Color Palette
The design system SHALL use Violet as the primary brand color instead of Sage Green.

#### Scenario: Primary button rendering
- **GIVEN** a primary action button
- **WHEN** rendered with default colorScheme
- **THEN** background color is Violet-500 (#7C3AED)
- **AND** hover state is Violet-600 (#6D28D9)
- **AND** active state is Violet-700 (#5B21B6)

#### Scenario: Primary focus ring
- **GIVEN** an interactive element receives focus
- **WHEN** focus ring is displayed
- **THEN** ring color is Violet-300 (#C4B5FD)
- **AND** ring has 2px offset

#### Scenario: Tag/chip styling
- **GIVEN** a default tag/chip component
- **WHEN** rendered
- **THEN** background is Violet-100 (#EDE9FE)
- **AND** text color is Violet-700 (#5B21B6)

### Requirement: Neutral Color Palette
The design system SHALL use Cool Gray for all neutral colors instead of Warm Stone.

#### Scenario: Page background
- **GIVEN** the main application page
- **WHEN** rendered
- **THEN** background color is Neutral-50 (#F9FAFB)

#### Scenario: Primary text
- **GIVEN** body text content
- **WHEN** rendered
- **THEN** color is Neutral-800 (#1F2937)
- **AND** NOT warm brown-gray (#292524)

#### Scenario: Secondary text
- **GIVEN** placeholder or secondary text
- **WHEN** rendered
- **THEN** color is Neutral-500 (#6B7280)

#### Scenario: Border colors
- **GIVEN** a bordered container
- **WHEN** rendered with default border
- **THEN** border color is Neutral-200 (#E5E7EB)

### Requirement: Selection State Styling
The design system SHALL use dashed purple borders for selected elements.

#### Scenario: Single node selection
- **GIVEN** user selects a canvas node
- **WHEN** node enters selected state
- **THEN** border style is `2px dashed #7C3AED`
- **AND** background color is Violet-50 (#F5F3FF)

#### Scenario: Sidebar item selection
- **GIVEN** user selects an item in sidebar list
- **WHEN** item enters selected state
- **THEN** border style is dashed with Violet-500
- **AND** background tint is Violet-50

#### Scenario: Multi-select consistency
- **GIVEN** user selects multiple nodes
- **WHEN** all selected nodes render
- **THEN** all have identical dashed border styling

### Requirement: Accent Color for Interactive Elements
The design system SHALL provide Rose/Coral accent color for likes, hearts, and notifications.

#### Scenario: Like button active state
- **GIVEN** a "like" button that is active (liked)
- **WHEN** rendered
- **THEN** icon color is Rose-500 (#F43F5E)

#### Scenario: Like count display
- **GIVEN** a like count badge
- **WHEN** count > 0
- **THEN** text color is Rose-500 (#F43F5E)

#### Scenario: Notification badge
- **GIVEN** a notification indicator
- **WHEN** unread count > 0
- **THEN** badge background is Rose-500 (#F43F5E)

### Requirement: Tab Active State
The design system SHALL use Violet for active tab indication, not red.

#### Scenario: Tab bar with active tab
- **GIVEN** a tab navigation component
- **WHEN** one tab is active
- **THEN** active tab text color is Violet-500 (#7C3AED)
- **AND** active tab has underline or background in Violet
- **AND** inactive tabs are Neutral-500 (#6B7280)

#### Scenario: Tab hover state
- **GIVEN** an inactive tab
- **WHEN** user hovers
- **THEN** text color transitions to Violet-400 (#A78BFA)

## ADDED Requirements

### Requirement: Accent Color Scale
The design system SHALL include a Rose/Coral accent scale for special interactive elements.

#### Scenario: Accent scale availability
- **GIVEN** the colors token file
- **WHEN** accessed
- **THEN** `colors.accent` contains full 50-900 scale
- **AND** accent.500 is #F43F5E

## Data Structures

### Color Palette Definition
```typescript
interface ColorPalette {
  primary: ColorScale;   // Violet (#7C3AED center)
  neutral: ColorScale;   // Cool Gray (#6B7280 center)
  accent: ColorScale;    // Rose (#F43F5E center)
  success: ColorScale;   // Green (unchanged)
  warning: ColorScale;   // Amber (unchanged)
  error: ColorScale;     // Red (unchanged)
  info: ColorScale;      // Blue (unchanged)
}

interface ColorScale {
  50: string;
  100: string;
  200: string;
  300: string;
  400: string;
  500: string;
  600: string;
  700: string;
  800: string;
  900: string;
  950?: string;
}
```

### Selection Style Definition
```typescript
interface SelectionStyle {
  border: string;        // "2px dashed #7C3AED"
  backgroundColor: string; // "#F5F3FF"
  focusRing: string;     // "#C4B5FD"
}
```

### Tab State Definition
```typescript
interface TabState {
  active: {
    color: string;       // Violet-500
    borderBottom: string; // "2px solid #7C3AED"
    background?: string;
  };
  inactive: {
    color: string;       // Neutral-500
  };
  hover: {
    color: string;       // Violet-400
  };
}
```

