# Tasks: Add Global Delete Confirmation and Error Notifications

## Phase 1: Core Components
- [ ] Create `NotificationContext` and `NotificationProvider` <!-- id: 300 -->
- [ ] Implement `useNotification` hook <!-- id: 301 -->
- [ ] Create `Toast` component for success/error alerts <!-- id: 302 -->
- [ ] Create `ConfirmDialog` reusable component <!-- id: 303 -->
- [ ] Inject `NotificationProvider` into `RootLayout` <!-- id: 304 -->

## Phase 2: dashboard Integration
- [ ] Replace local snackbar in `app/dashboard/page.tsx` with `useNotification` <!-- id: 305 -->
- [ ] Replace custom delete dialog with `ConfirmDialog` <!-- id: 306 -->

## Phase 3: Studio Integration
- [ ] Add error notification to `deleteChatSession` in `StudioContext.tsx` <!-- id: 307 -->
- [ ] Add error notification to `removeUrlContent` in `StudioContext.tsx` <!-- id: 308 -->
- [ ] Implement confirmation for document deletion in Sidebar <!-- id: 309 -->
- [ ] Implement confirmation for URL content deletion in Sidebar <!-- id: 310 -->
- [ ] Implement confirmation for chat session deletion in Chat List <!-- id: 311 -->

## Phase 4: Validation
- [ ] Verify success/error toasts appear correctly <!-- id: 312 -->
- [ ] Verify delete confirmation works for all target items <!-- id: 313 -->
- [ ] Verify "fail silently" logic is removed in favor of notifications <!-- id: 314 -->
