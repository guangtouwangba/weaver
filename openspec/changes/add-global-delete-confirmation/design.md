# Design: Global Delete Confirmation and Error Notifications

## Architecture

We will implement a global state management system for notifications and a standard pattern for confirmation dialogs.

### 1. Notification System
We will use React Context to manage a global notification stack (toast-style).

- **NotificationProvider**: Wrapped around the root layout. Manages a list of active notifications.
- **useNotification Hook**: Provides functions like `notifySuccess(msg)`, `notifyError(msg)`, and `showNotification(type, msg)`.
- **NotificationList Component**: Renders the active notifications in a fixed position (bottom-center or bottom-right).

### 2. ConfirmDialog Component
A specialized version of the existing `Dialog` component that simplifies the common "Confirm Action" pattern.

```tsx
interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isDanger?: boolean;
}
```

### 3. Integrated Deletion Logic
Updating `StudioContext.tsx` to include `confirmDelete` state or utility. However, to keep it clean, we can expose deletion methods that trigger the dialog if needed, or simply let the UI call the confirmation before calling the context's delete method.

**Preferred Pattern**:
1. Component (e.g. `DocumentListItem`) has local `isDeleteDialogOpen` state.
2. Clicks delete -> opens `ConfirmDialog`.
3. Confirms -> calls `context.deleteDocument()`.
4. `context.deleteDocument()` wraps the API call in a `try/catch`.
5. Error caught -> calls `notifyError()`.
6. Success -> calls `notifySuccess()`.

## Components Involved

### New Components
- `NotificationProvider`: Global context provider.
- `ConfirmDialog`: Reusable confirmation UI.
- `Toast`: Visual component for a single notification.

### Modified Files for Integration
- `app/layout.tsx`: Inject `NotificationProvider`.
- `app/dashboard/page.tsx`: Replace local snackbar with `useNotification`.
- `contexts/StudioContext.tsx`: Update deletion methods to return promises or trigger notifications.
- `components/studio/Sidebar.tsx` / `components/documents/DocumentListItem.tsx`: Add confirmation.
- `components/chat/ChatSessionList.tsx`: Add confirmation.
