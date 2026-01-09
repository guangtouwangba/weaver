# Contributing to Weaver

Thank you for your interest in contributing to Weaver! 🎉

## Getting Started

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/research-agent-rag.git
   ```
3. **Install dependencies**:
   ```bash
   make setup
   ```

## Development Workflow

### Branch Naming
- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring

### Making Changes

1. Create a new branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. Make your changes

3. Run tests and linting:
   ```bash
   make test
   make lint
   ```

4. Commit with clear messages:
   ```bash
   git commit -m "feat: add new feature description"
   ```

### Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance

## Pull Requests

1. Push to your fork
2. Open a PR against `main`
3. Fill out the PR template
4. Wait for review

## Code Style

- **Python**: Follow PEP 8, use Ruff for linting
- **TypeScript**: Use ESLint configuration

## Questions?

Open an issue or start a discussion!

## License

By contributing, you agree that your contributions will be licensed under the AGPL-3.0 License.
