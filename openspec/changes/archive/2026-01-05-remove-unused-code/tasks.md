## Phase 1: Backend Cleanup

### Curriculum Feature
- [x] Remove `api/v1/curriculum.py` and its router registration
- [x] Remove `application/use_cases/curriculum/` directory
- [x] Remove `application/dto/curriculum.py`
- [x] Remove `domain/entities/curriculum.py`
- [x] Remove `infrastructure/database/repositories/sqlalchemy_curriculum_repo.py`
- [x] Remove any curriculum-related Alembic migrations (if safe)

### Thinking Path Feature
- [x] Remove `api/v1/thinking_path.py` and its router registration
- [x] Remove `application/services/thinking_path_service.py`

## Phase 2: Frontend Cleanup
- [x] Remove `components/inbox/CreateProjectDialog.tsx` (duplicate)
- [x] Update `app/inbox/page.tsx` to import from `dialogs/CreateProjectDialog`

## Phase 3: Verification
- [x] Run `make lint` to ensure no broken imports
- [x] Run `make test` to ensure no test failures
- [x] Verify app builds and runs correctly
