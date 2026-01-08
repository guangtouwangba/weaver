# Tasks: Add Web Page Content Preview

## 1. Frontend: Web Page Card Enhancement (Canvas)

- [ ] 1.1 Verify `WebPageCard` displays all required elements (favicon, domain, badge, title, description, URL)
- [ ] 1.2 Add thumbnail display when `thumbnailUrl` is available in metadata
- [ ] 1.3 Ensure consistent card dimensions with YouTube/Video cards (~240px width)
- [ ] 1.4 Add loading placeholder for missing thumbnails with globe icon fallback
- [ ] 1.5 Add connection handles matching other canvas nodes

## 2. Frontend: Sidebar Web Page Preview

- [ ] 2.1 Create `WebPagePreviewPanel.tsx` component with article reader layout
- [ ] 2.2 Add click handler for web URL items in `ResourceSidebar.tsx` to trigger preview
- [ ] 2.3 Display web page thumbnail (hero image) at top of preview
- [ ] 2.4 Show article metadata (title, site name, author if available, published date)
- [ ] 2.5 Render extracted article content in scrollable reading area
- [ ] 2.6 Add "Open Original" button to visit source URL in new tab
- [ ] 2.7 Add "Add to Canvas" button to create web page node from preview

## 3. Frontend: Web Page Reader Modal

- [ ] 3.1 Create `WebPageReaderModal.tsx` component for immersive reading
- [ ] 3.2 Display full article content with comfortable reading typography
- [ ] 3.3 Add header with title, site info, and close button
- [ ] 3.4 Support Escape key to close modal
- [ ] 3.5 Add "Open in Browser" button to visit original URL

## 4. Frontend: Canvas Interaction

- [ ] 4.1 Add double-click handler on `WebPageCard` to open reader modal
- [ ] 4.2 Support standard canvas interactions (select, drag, delete, shift-click)
- [ ] 4.3 Add click handler for external link icon to open source URL

## 5. Frontend: Integration & Polish

- [ ] 5.1 Update `SourcePanel.tsx` to conditionally show web preview vs PDF viewer
- [ ] 5.2 Add smooth transitions between preview types
- [ ] 5.3 Handle empty/missing content gracefully with appropriate messages
- [ ] 5.4 Ensure consistent styling with Warm Stone design theme

