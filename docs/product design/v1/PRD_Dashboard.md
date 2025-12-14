# PRD: Dashboard (Landing Hub)

| Document Info | Details |
| --- | --- |
| **Version** | v1.0 |
| **Status** | Implemented |
| **Scope** | Dashboard Page (`/dashboard`) |

---

## 1. Overview
The Dashboard serves as the landing page and "Command Center" for the user. Its primary goal is to provide a high-level overview of work due and offer quick entry points into specific Knowledge Projects.

## 2. Layout Structure
The page utilizes a centered layout (`maxWidth: 1200px`) within the Global Layout.

### 2.1 Header Section
*   **Greeting**: Personalized welcome message ("Welcome back, Alex").
*   **Status Summary**: A text summary of immediate tasks (e.g., "You have 12 cards due for review today").
    *   *Future*: This will be driven by Spaced Repetition System (SRS) logic.

### 2.2 Smart Ingestion Zone
*   **Visuals**: A prominent, full-width dashed area.
*   **Function**: The primary "Start" action.
*   **Interactions**:
    *   **Drag & Drop**: Users can drag folders or files here to initialize a new project.
    *   **CTA Button**: "Create Project" button for manual creation.
    *   **Inbox Link**: Direct text link to jump to the Inbox for smaller items.

### 2.3 Active Projects Grid
*   **Layout**: Responsive Grid (`minmax(280px, 1fr)`).
*   **Card Content**:
    *   Project Title (e.g., "Project Alpha").
    *   Timestamp ("Last edited 2 mins ago").
*   **Interaction**:
    *   **Hover**: Border highlight (`primary.main`).
    *   **Click**: Navigates to the `/studio` or `/projects` view for that specific ID.
*   **Header**: Includes a "View All" link to the full Project List.

---

## 3. Functional Requirements
*   **Routing**: Cards must deep-link to the Studio context with the `projectId` pre-loaded.
*   **Responsiveness**: The grid must adapt gracefully from mobile (1 column) to desktop (3-4 columns).

