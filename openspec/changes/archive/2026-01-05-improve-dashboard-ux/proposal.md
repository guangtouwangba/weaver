# Proposal: Improve Dashboard UX

## Why
The current dashboard (Home Page) has received feedback regarding logical inconsistencies in navigation and visual noise in project cards. The goal is to refine the UI/UX to be more logical, cleaner, and accessible while maintaining the minimalist aesthetic.

## Goals
1.  **Resolve Navigation Conflict**: Unify the "Recent Projects" title vs. "All Projects" tab logic.
2.  **Optimize Card Design**: Remove visual noise (redundant avatars, grey placeholders) and improve information density.
3.  **Enhance Accessibility**: Improve text contrast for metadata.

## What Changes

### 1. Navigation & Filtering (The "Filter" Model)
-   Rename the main section title from "Recent Projects" to **"Projects"**.
-   Implement functional filtering for the Tabs:
    -   **All Projects**: Shows all projects sorted by `updated_at` (desc).
    -   **Recent**: Shows only projects from the last 7 days (or top 5).
    -   **Starred/Shared**: Filter by respective flags (future proofing).

### 2. Card Design Overhaul
-   **Thumbnail**: Replace the grey placeholder box with a **Colored Project Icon** (using the project name's initial) to add variety without complexity.
-   **Avatar**: Remove the user avatar from the card footer (it's redundant for personal workspaces).
-   **Description**: If empty, do **not** show "No description". Instead, show metadata (e.g., "Created on Dec 20").
-   **Contrast**: Darken the secondary text colors for better readability.

### 3. Visual Polish
-   Remove the pipe separator `|` in the header.
-   Ensure consistent time formatting (relative for recent, absolute for older).

## Risks
-   **Visual Empty State**: Without thumbnails, cards might look too plain. We will mitigate this with colorful generated icons.
