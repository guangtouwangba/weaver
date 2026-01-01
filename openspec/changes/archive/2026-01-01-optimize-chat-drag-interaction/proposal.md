# Optimize Chat Drag Interaction

## Why
The current "drag to chat" interaction places attached context chips below the chat input bar. This causes the entire chat interface to shift upwards when a file is dropped, which is visually jarring and disconnects the context from the input area. Users expect attached context to appear integrated with the input field, similar to modern chat interfaces (e.g., ChatGPT, Claude).

## What Changes
We will refactor the `AssistantPanel` to:
1.  Move the "Recent Context" (attached chips) *inside* the main Chat Input container.
2.  Display attached files/nodes as chips *above* the text input field but within the same visual boundary (or tightly coupled).
3.  Ensure the input container grows gracefully to accommodate attachments without shifting the entire UI awkwardly.
4.  Style the drop zone to be the entire input container, providing clear visual feedback.

## Impact Analysis
-   **User Experience**: Smoother, more predictable interaction when adding context. Input area feels more cohesive.
-   **Visuals**: The input bar will morph from a simple pill to a rounded container with attached items.
-   **Components**: `AssistantPanel.tsx` (primarily the render logic for input and context nodes).

## Mockup
![Chat Input Mockup](/Users/siqiuchen/.gemini/antigravity/brain/e5f6f67f-3ffb-46ae-a92e-be9584d88bb4/chat_input_mockup_1767255355143.png)
