# Studio

## ADDED Requirements

### Requirement: Smart Clipboard Export (Copy as Markdown)
The system SHALL allow users to copy selected nodes from the canvas to the system clipboard in Markdown format.

#### Scenario: Copy multiple nodes (Spatial Sequencing)
- **Given** multiple nodes are selected on the canvas
- **And** the nodes are arranged in a visual layout (rows/columns)
- **When** the user triggers the Copy action (`Ctrl+C` or `Cmd+C`)
- **Then** the system generates a Markdown representation of the selected content
- **And** the content is ordered based on "Visual Reading Order" (Top-to-Bottom, Left-to-Right)
- **And** the markdown is written to the system clipboard
- **And** a "Copied to clipboard" feedback is shown

#### Scenario: Copy Mindmap Structure
- **Given** a mindmap branch (Root + Children) is selected
- **When** the user copies the selection
- **Then** the output structure preserves hierarchy (using Headers `#` or List indentation `-`)
- **And** source references are converted to links/citations

#### Scenario: Copy Source Nodes
- **Given** a video or PDF source node is selected
- **When** the user copies it
- **Then** the output includes the Title, URL/Link, and relevant metadata (e.g., timestamp for video)
- **And** it is formatted as a rich block (e.g. Quote block with links)
