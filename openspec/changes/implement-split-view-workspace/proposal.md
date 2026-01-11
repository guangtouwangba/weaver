# Proposal: Implement Split View Workspace (UI/UX Pro Max)

## Goal
Elevate the Research Studio from a simple viewer to a **High-Performance Cognitive Workspace**. By introducing a persistent **Split View** layout and **Bi-directional Linking**, we enable a seamless "Read-Think-Map" loop that mirrors professional research workflows (like LiquidText or Obsidian Canvas), but specifically optimized for multimodal content (Video + PDF).

## Core Capabilities
1.  **Split View Grid**: A robust 3-pane layout (`Sidebar | Content | Canvas`) backed by `react-resizable-panels`.
2.  **Multimodal Content Dock**:
    - **PDF**: Integrated viewer with native text selection.
    - **Video**: "Transcript-First" player where subtitles are interactive first-class citizens.
3.  **Bi-directional Intelligence**:
    - **Drag-to-Link**: Create nodes by dragging text/transcript.
    - **Context Recall**: Clicking a node instantly restores the source context (scroll/seek).

## Value Proposition
The current modal-based viewing blocks user context, making it impossible to synthesize information in real-time. The new Split View Workspace unlocks **simultaneous consumption and production**, significantly reducing the cognitive load of switching contexts. The "Transcript-to-Canvas" interaction specifically solves the pain point of taking notes from video content.

## Visual Design Previews

The following mockups illustrate the proposed "Split View" layout and key interactions:

````carousel
![Split View Dashboard](/Users/siqiuchen/.gemini/antigravity/brain/10f806fb-e3f5-42b3-8689-9f018093c484/split_view_layout_mockup_1768099321570.png)
<!-- slide -->
![Video Transcript Interaction](/Users/siqiuchen/.gemini/antigravity/brain/10f806fb-e3f5-42b3-8689-9f018093c484/video_transcript_interaction_mockup_1768099337502.png)
<!-- slide -->
![Bi-directional Linking](/Users/siqiuchen/.gemini/antigravity/brain/10f806fb-e3f5-42b3-8689-9f018093c484/bidirectional_linking_mockup_1768099354121.png)
````
