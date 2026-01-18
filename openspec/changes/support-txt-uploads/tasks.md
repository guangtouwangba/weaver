# Tasks: Support .txt Uploads

- [x] Implement `TextParser` <!-- id: 1 -->
    - [x] Create `app/backend/src/research_agent/infrastructure/parser/text_parser.py`
    - [x] Register in `app/backend/src/research_agent/infrastructure/parser/factory.py`
- [x] Update Backend API <!-- id: 2 -->
    - [x] Update `app/backend/src/research_agent/api/v1/documents.py` to allow `.txt` uploads and `text/plain` content type.
- [x] Update Frontend <!-- id: 3 -->
    - [x] Add `.txt` to `acceptedFileTypes` in `app/frontend/src/components/dialogs/ImportSourceDialog.tsx`
- [x] Verification <!-- id: 4 -->
    - [x] Verify `.txt` upload works.
    - [x] Verify text extraction works.
