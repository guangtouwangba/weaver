# Proposal: Global Delete Confirmation and Error Notifications

## Goal
Implement a unified, global system for confirming destructive actions (like deletion) and notifying users of operation results (success/error). This ensures consistent UX across projects, documents, canvas nodes, and chat sessions.

## Context
Currently, deletion confirmation is inconsistent:
- Projects have a custom `Dialog` in `dashboard/page.tsx`.
- Documents and URL contents are removed immediately or fail silently in `StudioContext.tsx`.
- Chat sessions and sections are removed without confirmation.
- Error reporting for failed deletions is either local or missing.

## Proposed Solution
1. **ConfirmDialog Component**: A reusable component for asking for confirmation before proceeding with destructive actions.
2. **Notification System**: A global `NotificationProvider` and a `useNotification` hook to show "Toasts" (Snackbars) for success and error messages from anywhere in the app.
3. **Unified Deletion Pattern**: Update all deletion points to use the `ConfirmDialog` and report errors via `useNotification`.

## Impact
- **UX**: Prevents accidental data loss and provides clear feedback.
- **Maintainability**: Reduces duplicate dialog/snackbar logic in feature pages.
- **Reliability**: Ensures backend failures are visible to the user.
