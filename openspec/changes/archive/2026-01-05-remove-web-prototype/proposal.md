# Remove Web Directory (Prototype)

## Why
The project initially used `web/` for a prototype. The codebase has evolved, and the final production structure uses `app/frontend` and `app/backend`. Keeping the `web/` directory causes confusion, bloats the repository, and creates ambiguity for new contributors.

## What Changes
- The `web/` directory and all its contents will be deleted.
- Documentation references to `web/` in `openspec/project.md` will be updated to point to `app/frontend` and `app/backend`.

## Impact
- **Maintenance**: Cleaner repository structure and easier onboarding.
- **Documentation**: Accurate architectural overview.
- **Risk**: None, as the production code has already migrated to the `app/` directory and `Makefile` reflects this.
