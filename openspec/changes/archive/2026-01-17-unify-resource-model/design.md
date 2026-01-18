# Design: Unified Resource Model

## Context

The Visual Thinking Assistant currently manages content from multiple sources:
- PDF/Word/PPT documents via `DocumentModel`
- YouTube/Bilibili/Web URLs via `UrlContentModel`
- Inbox staging items via `InboxItemModel`

Each has its own:
- Database table and ORM model
- Repository interface
- API endpoints
- Frontend state management

When features like mindmap generation need to access content, they must explicitly handle each type, leading to the bug where YouTube videos couldn't generate mindmaps (only `DocumentModel` was queried).

## Goals
- **G1**: Single point of access for all content, regardless of storage backend
- **G2**: New content types can be added with minimal code changes
- **G3**: Existing APIs remain backward compatible during transition
- **G4**: Clear separation between resource metadata and content retrieval

## Non-Goals
- Full database migration in this phase (deferred to Phase 3)
- Breaking changes to existing APIs
- Changing frontend architecture (Phase 2)

## Decisions

### Decision 1: Resource as Domain Interface (not DB migration)

**Option A**: Migrate to single `resources` table
- Pros: Clean schema, single source of truth
- Cons: Complex migration, downtime risk, breaks existing queries

**Option B**: Add Resource abstraction layer over existing models ✅
- Pros: Zero migration risk, backward compatible, progressive adoption
- Cons: Slight complexity in resolution layer

**Decision**: Option B - Create `Resource` domain entity and `ResourceResolver` that queries appropriate underlying model based on ID prefix or type registry.

### Decision 2: Resource ID Format

**Option A**: Prefixed IDs (e.g., `doc_xxx`, `url_xxx`)
- Pros: Self-describing, no lookup needed to determine type
- Cons: Requires ID migration or wrapper

**Option B**: Registry-based lookup with unprefixed UUIDs
- Pros: No ID changes, works with existing data
- Cons: May require multiple DB queries to find resource

**Option C**: Composite ID with metadata (e.g., `{"type": "document", "id": "xxx"}`) ✅
- Pros: Explicit, no migration, single-query resolution
- Cons: Slightly more complex API payload

**Decision**: Option C for new APIs, with helper to auto-detect type for legacy UUIDs by checking tables.

### Decision 3: Content Access Pattern

```python
@dataclass
class Resource:
    """Unified resource abstraction."""
    id: UUID
    type: ResourceType  # document, url_content, inbox_item
    title: str
    content: Optional[str]  # Extracted/full content
    summary: Optional[str]  # AI-generated summary
    metadata: Dict[str, Any]  # Type-specific metadata
    thumbnail_url: Optional[str]
    source_url: Optional[str]
    created_at: datetime
    updated_at: datetime

class ResourceResolver:
    """Resolves resource IDs to unified Resource objects."""
    
    async def resolve(self, resource_id: UUID, type_hint: Optional[str] = None) -> Optional[Resource]:
        """Resolve a single resource by ID."""
        # Try type hint first, then fall back to auto-detection
        
    async def resolve_many(self, resource_ids: List[UUID]) -> List[Resource]:
        """Resolve multiple resources, auto-detecting types."""
        
    async def get_content(self, resource_id: UUID) -> str:
        """Get content for a resource (primary use case)."""
```

### Decision 4: ResourceType Enum (Content Category, Not Platform)

**Key Insight**: ResourceType should represent the **content category**, not the source/platform. Platform is metadata.

```python
class ResourceType(str, Enum):
    """Content category-based resource types."""
    
    # Text-based content
    DOCUMENT = "document"  # PDF, Word, PPT, Markdown, plain text
    WEB_PAGE = "web_page"  # Articles, blog posts, web content
    NOTE = "note"          # User-created notes in the system
    
    # Media content
    VIDEO = "video"        # All video: local files, YouTube, Bilibili, Douyin
    AUDIO = "audio"        # All audio: local files, podcasts, voice memos
    IMAGE = "image"        # Images, diagrams, screenshots
    
    # Special types
    COLLECTION = "collection"  # Grouped resources (future)


# Platform is stored in metadata, not type
@dataclass
class Resource:
    id: UUID
    type: ResourceType           # e.g., VIDEO
    title: str
    content: Optional[str]
    metadata: Dict[str, Any]     # Contains platform: "youtube" | "bilibili" | "local" | etc.
    thumbnail_url: Optional[str]
    source_url: Optional[str]    # External URL or None for local
    created_at: datetime
    updated_at: datetime
```

**Rationale**:
- A YouTube video and a local MP4 are both "videos" - same content type, different source
- Processing logic can be unified by content type (all videos → extract transcript)
- Platform-specific handling is encapsulated in adapters, not scattered in type checks
- Adding a new video platform (e.g., TikTok) doesn't require new ResourceType

## Implementation Plan

### Phase 1: Abstraction Layer

1. Create `domain/entities/resource.py`:
   - `Resource` dataclass
   - `ResourceType` enum

2. Create `infrastructure/resource_resolver.py`:
   - `ResourceResolver` class
   - Adapters for each existing model

3. Modify `output_generation_service.py`:
   - Use `ResourceResolver.get_content()` instead of direct model queries
   - Accept `resource_ids` alongside legacy `document_ids`

4. Modify chat streaming:
   - Use `ResourceResolver` for context loading

### Phase 2: API Unification (Future)

1. New request format:
```json
{
  "output_type": "mindmap",
  "resources": [
    {"id": "uuid-1"},
    {"id": "uuid-2", "type": "youtube"}
  ]
}
```

2. Frontend unified state:
```typescript
const { resources } = useStudio();
// resources: Resource[] includes all content types
```

### Phase 3: Database Unification (Future)

1. Create `resources` table with polymorphic type
2. Migrate existing data
3. Deprecate old models

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Performance: Multiple DB queries for type detection | Use type hints when available, batch queries |
| Complexity: New abstraction layer | Keep interface minimal, well-documented |
| Backward compatibility | Maintain old APIs, deprecate gradually |

## Open Questions

1. Should we expose resource type in frontend routing (e.g., `/studio/:projectId/resource/:type/:id`)?
2. How to handle resources that exist in multiple models (e.g., imported URL that became a document)?
3. Should `InboxItemModel` be a first-class resource or just a staging area?

