# Tasks: Hide Inspiration Dock on Generate

## Implementation

- [x] **1. Update dock visibility condition in InspirationDock.tsx**
  - Modify condition at L249-250 to add `!hasActiveGenerations()` check

## Verification

- [x] **2. Manual test**
  - Open studio with a document uploaded
  - Click "Summary" button
  - Verify dock hides immediately during generation
