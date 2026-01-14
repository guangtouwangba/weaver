# Change: Add Custom Model Support

## Why

Currently, users can only select from a hardcoded list of LLM models in the settings page. Power users who have access to custom model endpoints (e.g., self-hosted models, fine-tuned models, or less common OpenRouter models) cannot use them with the application.

## What Changes

- **[NEW]** Add `custom_models` database table to store user-defined custom models
- **[MODIFY]** Backend settings API to support CRUD for custom models
- **[MODIFY]** Settings service to merge custom models with built-in model options
- **[MODIFY]** Frontend settings page to display models in a **list layout** instead of grid
- **[NEW]** Add UI for creating/editing/deleting custom models

## Impact

- **Affected specs**: `settings` (new capability)
- **Affected code**:
  - `app/backend/src/research_agent/infrastructure/database/models.py` - new `CustomModelModel`
  - `app/backend/src/research_agent/domain/services/settings_service.py` - custom model logic
  - `app/backend/src/research_agent/api/routes/settings.py` - new endpoints
  - `app/frontend/src/app/settings/page.tsx` - UI changes (grid → list)
  - `app/frontend/src/lib/api.ts` - API client additions
  - New Alembic migration for database schema
