# Contributing

## Getting Started

1. Fork the repository and clone your fork.
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow the development setup in [docs/development.md](docs/development.md).
4. Make your changes with tests.
5. Ensure linters pass (flake8/black, checkstyle, phpcs, rubocop, eslint).
6. Submit a Pull Request targeting `develop`.

## Code Style

- **Python**: PEP 8, formatted with `black`, linted with `flake8`.
- **Java**: Google Java Style (enforced by Checkstyle).
- **PHP**: PSR-12.
- **Ruby**: RuboCop defaults.
- **JavaScript/TypeScript**: ESLint with project config.

## Commit Messages

Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `test:`.

## Pull Requests

- Link the related issue.
- Include a description of changes and testing done.
- All CI checks must pass before merge.
- At least one maintainer approval required.

## Reporting Issues

Open a GitHub Issue with steps to reproduce, expected vs actual behavior, and environment details.
