# Design: Mind Map Persistence API

## API Implementation

### Endpoint
`PATCH /api/v1/projects/{project_id}/outputs/{output_id}`

### Request Body
```json
{
  "title": "Optional new title",
  "data": { ... } // Updated MindmapData JSON blob
}
```

### Response
Returns the updated `OutputResponse` object.

## Considerations
- **Concurrency**: We are assuming last-write-wins for now. Given this is a single-user studio experience mostly, this is acceptable.
- **Data Size**: Mind map JSONs are typically small (< 1MB). Sending full JSON on save is efficient enough and avoids complexity of JSON-patch or OT.
- **Validation**: Backend should minimally validate that `data` is a valid JSON object, but strict schema validation of nodes/edges might be overkill for this generic storage layer, unless we use the Pydantic models derived from `MindmapData`.
