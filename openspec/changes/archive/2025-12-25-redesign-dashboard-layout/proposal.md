# Change: Redesign Dashboard Layout

## Why
The current dashboard provides basic project listing but lacks visual hierarchy and quick-start capabilities. A redesign is needed to improve user experience, offer easier access to recent work, and provide templates for faster project initiation. The new design aligns with a cleaner, more modern aesthetic.

## What Changes
- **New Layout**: Three distinct sections (Header, Recent Projects, Start from Template).
- **Header**: Personalized welcome message and primary actions (Import, Create New Project).
- **Recent Projects**: Visual cards displaying the most recently modified projects.
- **Templates**: Predefined templates (Market Analysis, Brainstorming, Roadmap, Retrospective) to bootstrap new projects.
- **Project List**: Tabbed interface for filtering projects (All, Starred, Shared).
- **Styling**: Updated theme with lighter backgrounds, dot pattern, and refined typography.

## Impact
- **Affected Specs**: `dashboard`
- **Affected Code**: 
    - `app/frontend/src/app/dashboard/page.tsx`
    - `app/frontend/src/theme/theme.ts`
    - `app/frontend/src/app/globals.css`
    - New components in `app/frontend/src/components/dashboard/`

