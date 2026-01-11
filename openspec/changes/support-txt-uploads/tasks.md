# Tasks: Support .txt Uploads

- [ ] Implement `TextParser` <!-- id: 1 -->
    - [ ] Create `app/backend/src/research_agent/infrastructure/parser/text_parser.py`
    - [ ] Register in `app/backend/src/research_agent/infrastructure/parser/factory.py`
- [ ] Update Backend API <!-- id: 2 -->
    - [ ] Update `app/backend/src/research_agent/api/v1/documents.py` to allow `.txt` uploads and `text/plain` content type.
- [ ] Update Frontend <!-- id: 3 -->
    - [ ] Add `.txt` to `acceptedFileTypes` in `app/frontend/src/components/dialogs/ImportSourceDialog.tsx`
- [ ] Verification <!-- id: 4 -->
    - [ ] Verify `.txt` upload works.
    - [ ] Verify text extraction works.
