# PRD: Inbox (Capture & Triage)

| Document Info | Details |
| --- | --- |
| **Version** | v1.0 |
| **Status** | Implemented |
| **Scope** | Inbox Page (`/inbox`) |

---

## 1. Overview
The Inbox is a specialized interface for **Capture** and **Triage**. It separates the flow of collecting raw ideas/links from the deep work of processing them. It uses a "Pile vs. Triage" split-screen metaphor.

## 2. Layout Architecture
The page uses a **Split-Pane Layout** (Fixed Left, Flexible Right).

### 2.1 Left Column: The Pile (Capture)
*   **Width**: Fixed 400px.
*   **Header**:
    *   Inbox Icon + Counter Badge.
    *   Quick Capture Input: A `TextField` with a "+" button to instantly add thoughts or URLs.
*   **The List**:
    *   Scrollable list of pending items.
    *   **Visuals**: Each item is a card showing an icon (PDF/Audio/Link), title, and relative time ("10 mins ago").
    *   **Selection State**: Active item has a highlighted background (`#F8FAFC`) and primary border.
*   **Empty State**: "Inbox Zero" illustration when the list is cleared.

### 2.2 Right Column: Triage Station (Process)
*   **Function**: Detailed review and decision making for the selected item.
*   **Components**:
    1.  **Preview Area**: A placeholder (300px height) for quickly viewing the content (e.g., embedded PDF first page).
    2.  **AI Analysis Card**:
        *   **Badge**: "AI ANALYSIS" label.
        *   **Summary**: A generated 1-sentence summary of the content.
        *   **Suggested Action**: The AI proposes a destination project based on context.
*   **Action Buttons**:
    *   **Move to Project**: Primary action. Accepts the AI suggestion.
    *   **Other Project**: Opens a picker to override the suggestion.
    *   **Delete**: Discards the item.

---

## 3. Interaction Logic
1.  **Selection**: Clicking an item in the Left Column populates the Right Column.
2.  **Processing**:
    *   Clicking "Move" or "Delete" triggers `handleProcess(id)`.
    *   **Auto-Advance**: The system automatically removes the processed item and selects the next one in the list.
    *   **Zero State**: If the last item is processed, the Right Column shows a "Select an item" placeholder (or effectively clears if the list is empty).

## 4. Data Model (Item)
*   `id`: Unique identifier.
*   `type`: `pdf` | `link` | `audio`.
*   `title`: Display name.
*   `summary`: AI-generated synopsis.
*   `suggestedProject`: Target project ID/Name.
*   `confidence`: `High` | `Low` (Visualized in future versions).

