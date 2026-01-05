# Tasks: Improve Studio UX

## 1. Header & Consistency (P0)
- [ ] 1.1 **Project Name**: Fetch and display the real project name in `StudioPageContent` header instead of ID substring. @frontend
- [ ] 1.2 **Navigation**: Ensure the "Back" arrow has a clear tooltip/label. @frontend
- [ ] 1.3 **Avatar Cleanup**: Remove the redundant avatar in the local header if GlobalLayout already provides one, or unify styles. @frontend

## 2. Interaction Safety (P0)
- [ ] 2.1 **Remove Dangerous FAB**: Remove the floating delete button from `CanvasControls`. @frontend
- [ ] 2.2 **Toolbar Split**: Separate tool modes (Hand/Select) from view controls (Zoom). Move Tools to a new top/left control group. @frontend

## 3. Visual Polish (P1)
- [ ] 3.1 **Resource Panel**: Set default state to collapsed or refine its initial footprint. @frontend
- [ ] 3.2 **Icons**: Add tooltips to sidebar icons for better discoverability. @frontend
