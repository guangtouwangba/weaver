from research_agent.domain.skills import Skill

SRP_SKILL = Skill(
    name="Semantic Reconstruction Protocol (SRP)",
    description="A mindmap generation protocol for converting unstructured information into high-structure visual knowledge maps.",
    instruction="""
You are equipped with the **Semantic Reconstruction Protocol (SRP)**. This is a standard operating procedure for converting unstructured information into high-structure mental models.

#### 1. Core Cognitive Models
- **Cognitive Load Control**: Use "chunking" to break down complex information into manageable groups (7±2 items).
- **The DIKW Pyramid**: Distinguish between Data, Information, Knowledge, and Wisdom. Focus on Knowledge and Wisdom for core nodes.
- **Constructivism**: Don't just copy information; reconstruct meaning. The map reflects understanding, not just a table of contents.

#### 2. Standard Operating Procedure

##### Phase I: Meta-Structural Surveying
- **Define Scope**: Ask "What specific problem does this mindmap solve?" (SCQA framework).
- **Identify BOIs**: specific 3-5 Basic Ordering Ideas that govern the entire text.

##### Phase II: Signal Acquisition & Denoising
- **Progressive Summarization**: Capture -> Organize -> Distill -> Express.
- **Keyword Extraction**: Exclude stop words. Lock onto "high-weight words" (domain terms, verbs).
- **Rule**: 1-3 words per node. Avoid long paragraphs.

##### Phase III: Logical Architecture
- **MECE Principle**: Mutually Exclusive, Collectively Exhaustive. Check branches for overlap or gaps.
- **Pyramid Principle**: Parent nodes must summarize child nodes. Child nodes should be ordered logically (time, structure, importance).
- **Integration**: Synthesize sources into a neutral terminology system.

##### Phase IV: Visual Encoding
- **Space Layout**: Use "Proximity" principle. Group related concepts visually.

#### 3. Quality Checklist
- [ ] **Centrality**: One clear central topic?
- [ ] **MECE**: Are first-level branches independent and exhaustive?
- [ ] **Keywords**: Are nodes concise keywords, not sentences?
- [ ] **Hierarchy**: Do parent nodes accurately summarize children?
""",
)
