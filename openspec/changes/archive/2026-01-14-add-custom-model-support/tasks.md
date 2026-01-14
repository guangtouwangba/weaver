# Tasks: Add Custom Model Support

## 1. Database Schema
- [x] 1.1 Create `CustomModelModel` in `models.py` with fields: `id`, `user_id`, `model_id`, `label`, `description`, `provider`, `is_active`, `created_at`, `updated_at`
- [x] 1.2 Create Alembic migration for `custom_models` table
- [x] 1.3 Run migration locally and verify table structure

## 2. Backend Domain Layer
- [x] 2.1 Add `ICustomModelRepository` interface in `domain/repositories/`
- [x] 2.2 Implement `CustomModelRepository` in `infrastructure/database/`
- [x] 2.3 Create `CustomModelService` for CRUD operations
- [x] 2.4 Update `SettingsService.get_metadata()` to merge custom models with built-in options

## 3. Backend API Layer
- [x] 3.1 Add `GET /api/v1/settings/custom-models` endpoint (list user's custom models)
- [x] 3.2 Add `POST /api/v1/settings/custom-models` endpoint (create custom model)
- [x] 3.3 Add `PUT /api/v1/settings/custom-models/{id}` endpoint (update custom model)
- [x] 3.4 Add `DELETE /api/v1/settings/custom-models/{id}` endpoint (delete custom model)

## 4. Frontend API Client
- [x] 4.1 Add `customModelsApi` methods in `lib/api.ts`

## 5. Frontend UI Changes
- [x] 5.1 Change model selection from grid layout (`StrategyCard`) to vertical list layout
- [x] 5.2 Add "Add Custom Model" button below model list
- [x] 5.3 Create modal/dialog for adding/editing custom models
- [x] 5.4 Add delete confirmation for custom models
- [x] 5.5 Display custom models in the list with edit/delete actions

## 6. Verification
- [x] 6.1 Manual test: Create, view, update, delete custom model
- [x] 6.2 Manual test: Select custom model and verify it persists
- [x] 6.3 Manual test: Verify list layout displays correctly
