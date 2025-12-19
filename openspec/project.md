# Project Context

## Purpose

<!-- TODO: Describe your project purpose here -->

### Workflow

<!-- TODO: Describe the main user workflow -->

## Tech Stack

<!-- TODO: List your technologies -->
- **Language:**
- **Framework:**
- **Database:**
- **Hosting:**

## Project Conventions

### Code Style
- Formatter: (e.g., Black, Prettier)
- Linting: (e.g., Ruff, ESLint)
- Naming: snake_case for functions/variables, PascalCase for classes
- Strict type hints required on all public functions

### Architecture Patterns
- Layered architecture: handlers -> services -> repositories
- Async-first design (if applicable)
- Dependency injection for services
- Configuration via environment variables

### Testing Strategy
- Test framework: (e.g., pytest, jest)
- Minimum coverage target: 80%
- Mock external APIs in tests

### Git Workflow
- Main branch: `main` (protected, auto-deploy)
- Dev branch: `dev` (development)
- Feature branches: `feature/[description]`
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

## Domain Context

<!-- TODO: Define key domain terms -->

## Important Constraints

<!-- TODO: List technical constraints -->

## External Dependencies

<!-- TODO: List external APIs and services -->
