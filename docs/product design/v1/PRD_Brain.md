# PRD: The Brain (Global Knowledge Graph)

| Document Info | Details |
| --- | --- |
| **Version** | v1.0 |
| **Status** | Implemented |
| **Scope** | Brain Page (`/brain`) |

---

## 1. Overview
**The Brain** provides a bird's-eye view of the user's entire knowledge base. Unlike the Studio (which focuses on one project), the Brain visualizes connections **across** multiple projects, revealing hidden patterns and bridges between disciplines (e.g., NLP vs. Biology).

## 2. Layout & Visualization
The page is dominated by a full-screen interactive SVG graph.

### 2.1 Canvas Environment
*   **Background**: Matches the Studio's dotted grid for consistency (`radial-gradient`), providing a sense of unified space.
*   **Navigation**: Supports panning (future) and static coordinate visualization currently.

### 2.2 Node Visualization
*   **Representation**: SVG Circles (`r=8`) with text labels.
*   **Color Coding**: Nodes are colored by their Project source (e.g., Blue for NLP, Green for Bio).
*   **Special Nodes**:
    *   **Bridge Nodes**: Concepts that link two disparate projects (e.g., "Neural Plasticity"). Rendered with a special glow/highlight.
    *   **Selection**: Selected nodes show a "Glow" effect (`opacity=0.15` ring).

### 2.3 Heads-Up Display (HUD)
*   **Search Bar**: Floating top-center. Pill-shaped. Includes "Filter" button.
*   **Stats Chips**: Display global metrics (e.g., "12 Projects", "1,240 Concepts", "85 Connections").
*   **Legend**: Bottom-left list indicating which color corresponds to which project.

---

## 3. Feature Specifications: Insight Panel
When a node is selected, a floating panel appears on the right.

### 3.1 Content
*   **Header**: Node color + Label.
*   **Context**: "Appears in Project: [Project Name]" (with deep link capability).
*   **AI Insight**: A specific section where the AI explains *why* this node is important or how it bridges two concepts.
    *   *Example*: "This concept links NLP and Biology. It suggests that Attention might share mechanics with Synaptic Plasticity."

### 3.2 Interactions
*   **Open Project**: A button to jump directly to the Studio view for that project, focusing on this specific node.

---

## 4. Data Structure
*   **Node**: `{ id, label, project, type, x, y, color }`
*   **Link**: `{ sourceId, targetId }` (Rendered as dashed lines to indicate loose coupling compared to Studio's solid logic lines).

