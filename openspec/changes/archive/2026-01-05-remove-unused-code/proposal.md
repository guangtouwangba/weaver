# Remove Unused Code

## Why
The codebase contains code that was written but never integrated into the product. This dead code:
- Increases maintenance burden
- Confuses contributors
- Creates false impressions of feature availability
- May cause issues during refactoring

## What Changes
Remove backend API routes and their associated code that have no frontend usage:

### Backend (Priority)
1. **Curriculum API** (`api/v1/curriculum.py`)
   - No frontend calls to `/api/v1/curriculum/*`
   - Associated use cases: `application/use_cases/curriculum/`
   - Associated DTOs: `application/dto/curriculum.py`
   - Associated entities: `domain/entities/curriculum.py`
   - Associated repository: `infrastructure/database/repositories/sqlalchemy_curriculum_repo.py`

2. **Thinking Path API** (`api/v1/thinking_path.py`)
   - No frontend calls to `/api/v1/thinking-path/*`
   - Associated service: `application/services/thinking_path_service.py`

### Frontend
1. **Duplicate CreateProjectDialog** (`components/inbox/CreateProjectDialog.tsx`)
   - Same component exists in `components/dialogs/CreateProjectDialog.tsx`
   - Inbox page should import from `dialogs/`

## Impact
- **Reduced codebase size**: ~1500 lines of Python, ~100 lines TypeScript
- **Simpler API surface**: Fewer routes to document/maintain
- **Clearer feature scope**: Only functional features remain

## Risks
- **Future plans**: These features may have been planned but not yet connected. Verify with product roadmap before deletion.
