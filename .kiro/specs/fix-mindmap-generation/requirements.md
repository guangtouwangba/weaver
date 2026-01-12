# Requirements Document

## Introduction

本规范旨在解决 mindmap 生成功能中的三个关键问题：
1. 生成的节点可能会重叠
2. 解析出来的节点存在多个主题（多个根节点）
3. mindmap 生成会一直处于 loading 状态，需要手动刷新才能展示结果

## Glossary

- **Mindmap_Parser**: 前端 markdown 解析器，负责将后端返回的 markdown 格式转换为 MindmapNode 和 MindmapEdge 结构
- **Layout_Algorithm**: 布局算法模块，负责计算节点位置以避免重叠
- **Generation_Task**: 生成任务状态管理，跟踪 mindmap 生成的进度和完成状态
- **WebSocket_Handler**: WebSocket 消息处理器，负责接收后端流式数据并更新前端状态
- **Root_Node**: 思维导图的根节点，depth 为 0 且没有 parentId

## Requirements

### Requirement 1: 节点重叠预防

**User Story:** As a user, I want the generated mindmap nodes to be properly spaced without overlapping, so that I can clearly see and read all the content.

#### Acceptance Criteria

1. WHEN the Layout_Algorithm applies layout to mindmap nodes, THE Layout_Algorithm SHALL ensure minimum spacing of 40px vertically and 80px horizontally between adjacent nodes
2. WHEN nodes have varying content lengths, THE Layout_Algorithm SHALL dynamically calculate node heights and adjust spacing accordingly
3. WHEN a subtree has many children, THE Layout_Algorithm SHALL expand the vertical space to accommodate all children without overlap
4. IF two nodes would overlap after initial layout calculation, THEN THE Layout_Algorithm SHALL recursively adjust positions until no overlaps exist

### Requirement 2: 单一根节点保证

**User Story:** As a user, I want the mindmap to have a single clear root topic, so that the structure is coherent and easy to understand.

#### Acceptance Criteria

1. WHEN the Mindmap_Parser parses markdown content, THE Mindmap_Parser SHALL identify exactly one root node (the first heading)
2. WHEN the markdown contains multiple top-level headings (multiple # lines), THE Mindmap_Parser SHALL treat only the first heading as root and subsequent headings as children
3. WHEN parsing is complete, THE Mindmap_Parser SHALL validate that exactly one node has depth=0 and no parentId
4. IF multiple potential root nodes are detected, THEN THE Mindmap_Parser SHALL merge them under a single synthesized root or connect subsequent roots as children of the first

### Requirement 3: 生成完成状态同步

**User Story:** As a user, I want to see the mindmap result immediately when generation completes, so that I don't have to manually refresh the page.

#### Acceptance Criteria

1. WHEN the WebSocket_Handler receives a 'generation_complete' event, THE WebSocket_Handler SHALL immediately update the mindmap result state
2. WHEN the Generation_Task completes, THE Generation_Task SHALL trigger a React state update that causes immediate re-render
3. WHEN layout is applied to final data, THE Layout_Algorithm SHALL return the result synchronously without additional async operations
4. WHEN completeGeneration is called, THE StudioContext SHALL update canvasNodes state in the same render cycle
5. IF the WebSocket connection closes before completion, THEN THE WebSocket_Handler SHALL fall back to polling and still update state correctly upon completion

### Requirement 4: 布局算法优化

**User Story:** As a user, I want the mindmap layout to be visually balanced and readable, so that I can quickly understand the document structure.

#### Acceptance Criteria

1. WHEN applying balanced layout, THE Layout_Algorithm SHALL distribute children evenly on left and right sides of the root
2. WHEN calculating subtree height, THE Layout_Algorithm SHALL account for actual node content height, not just default height
3. WHEN positioning nodes, THE Layout_Algorithm SHALL maintain consistent parent-child visual hierarchy
4. THE Layout_Algorithm SHALL complete layout calculation for up to 200 nodes within 100ms

### Requirement 5: Markdown 解析健壮性

**User Story:** As a user, I want the mindmap to correctly parse various markdown formats from the LLM, so that the structure accurately reflects the document content.

#### Acceptance Criteria

1. WHEN parsing markdown with mixed heading levels (##, ###, ####), THE Mindmap_Parser SHALL correctly establish parent-child relationships based on heading depth
2. WHEN parsing markdown with bullet points under headings, THE Mindmap_Parser SHALL attach bullets as children of the nearest preceding heading
3. WHEN encountering malformed markdown (missing root heading), THE Mindmap_Parser SHALL create a default root node with title "Overview"
4. WHEN parsing source markers [PAGE:X] or [TIME:MM:SS], THE Mindmap_Parser SHALL extract them correctly and attach to the node's sourceRefs
