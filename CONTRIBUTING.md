# Contributing to Grafana Publisher

## 🌳 Git Workflow

### Branch Strategy

We follow a simplified Git Flow:

- **`main`** - Production branch (stable releases)
  - Only contains tested, production-ready code
  - Releases are tagged as `v0.1.0`, `v0.2.0`, etc.
  - Direct commits are NOT allowed (only via PR)

- **`develop`** - Development branch (pre-releases)
  - Integration branch for features
  - Releases are tagged as `v0.2.0-develop.1`, etc.
  - Features are merged here first for testing

- **`feature/*`** - Feature branches
  - Created from `develop`
  - Merged back to `develop` via PR
  - Naming: `feature/add-jira-support`, `feature/improve-auth`

- **`hotfix/*`** - Hotfix branches
  - Created from `main` for critical fixes
  - Merged to both `main` AND `develop`
  - Naming: `hotfix/fix-critical-bug`

### Workflow Example

```bash
# 1. Start a new feature
git checkout develop
git pull origin develop
git checkout -b feature/add-new-command

# 2. Work on your feature
git add .
git commit -m "feat: add new command for X"

# 3. Keep up to date with develop
git fetch origin
git rebase origin/develop

# 4. Push and create PR
git push origin feature/add-new-command
gh pr create --base develop

# 5. After PR is merged, delete local branch
git checkout develop
git pull origin develop
git branch -d feature/add-new-command
```

## 📝 Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) for automatic versioning:

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | Minor (0.x.0) |
| `fix` | Bug fix | Patch (0.0.x) |
| `docs` | Documentation only | No bump |
| `style` | Code style (formatting) | No bump |
| `refactor` | Code refactoring | No bump |
| `perf` | Performance improvement | Patch |
| `test` | Adding tests | No bump |
| `chore` | Build process/tools | No bump |
| `ci` | CI/CD changes | No bump |

### Breaking Changes

Add `!` after type or `BREAKING CHANGE:` in footer for major version bump:

```bash
feat!: redesign configuration system

BREAKING CHANGE: Configuration file format has changed
```

### Examples

```bash
# Feature (minor bump)
git commit -m "feat: add support for Jira integration"

# Bug fix (patch bump)
git commit -m "fix: resolve timeout issue in Grafana API"

# Breaking change (major bump)
git commit -m "feat!: change config file format to TOML"

# With scope
git commit -m "feat(clickup): add custom field mapping"

# With body
git commit -m "fix: resolve memory leak in alert processor

The alert processor was keeping references to old alerts.
This commit adds proper cleanup after processing.

Fixes #123"
```

## 🚀 Release Process

### Development Releases (Continuous)

Every merge to `develop` creates a pre-release automatically:

```bash
# Automatic on merge to develop
v0.2.0-develop.1
v0.2.0-develop.2
v0.2.0-develop.3
```

### Production Releases (Planned)

1. **Prepare Release**
   ```bash
   # Ensure develop is stable
   git checkout develop
   git pull origin develop
   
   # Run all tests
   make test
   make lint
   ```

2. **Create Release PR**
   ```bash
   # Create PR from develop to main
   gh pr create \
     --base main \
     --head develop \
     --title "Release v0.3.0" \
     --body "## Changes
   - feat: auto-upgrade system
   - fix: API timeout issues
   
   ## Testing
   - [x] All tests pass
   - [x] Manual testing completed
   - [x] Documentation updated"
   ```

3. **Review & Merge**
   - Code review by at least one maintainer
   - CI/CD checks must pass
   - Merge (triggers automatic release)

4. **Post-Release**
   ```bash
   # Update develop with main
   git checkout develop
   git pull origin main
   git push origin develop
   ```

## 🏷️ Versioning Strategy

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
  - **MAJOR**: Breaking changes
  - **MINOR**: New features (backward compatible)
  - **PATCH**: Bug fixes

### Version Lifecycle

```
develop: 0.2.0-develop.1
   ↓ (feature added)
develop: 0.3.0-develop.1
   ↓ (more commits)
develop: 0.3.0-develop.2
   ↓ (release to main)
main: 0.3.0
   ↓ (hotfix)
main: 0.3.1
```

## 📋 Release Checklist

Before releasing to production (`main`):

- [ ] All tests pass (`make test`)
- [ ] Code is linted (`make lint`)
- [ ] Documentation is updated
- [ ] CHANGELOG is up to date
- [ ] Version bump makes sense
- [ ] No sensitive data in code
- [ ] Dependencies are updated
- [ ] Security vulnerabilities checked
- [ ] Manual testing completed
- [ ] PR has been reviewed

## 🔄 Hotfix Process

For critical production bugs:

```bash
# 1. Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/fix-critical-issue

# 2. Fix the issue
git commit -m "fix: resolve critical production issue"

# 3. Create PR to main
gh pr create --base main --title "Hotfix: Critical issue"

# 4. After merge, sync with develop
git checkout develop
git pull origin main
git push origin develop
```

## 🤝 Pull Request Guidelines

### PR Title Format
Follow conventional commits:
- `feat: add new feature`
- `fix: resolve bug`
- `docs: update README`

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

## 🛠️ Development Setup

```bash
# Clone repository
git clone https://github.com/jStrider/grafana-publisher.git
cd grafana-publisher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .  # Install in development mode

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_clickup.py

# Run linting
ruff check .
black --check .

# Format code
ruff check . --fix
black .
```

## 📚 Documentation

- Update docstrings for new functions/classes
- Update README.md for user-facing changes
- Update CONTRIBUTING.md for process changes
- Add examples for new features

## 🔒 Security

- Never commit secrets or API keys
- Use environment variables for sensitive data
- Report security issues privately to maintainers
- Keep dependencies updated

## 💡 Tips

1. **Keep PRs small and focused** - One feature/fix per PR
2. **Write descriptive commit messages** - Help future maintainers
3. **Test locally first** - Don't rely only on CI
4. **Document breaking changes** - Be explicit about impacts
5. **Rebase, don't merge** - Keep history clean
6. **Delete merged branches** - Keep repository tidy

## 📊 Release Frequency

- **Development releases**: Continuous (on each merge to develop)
- **Production releases**: Bi-weekly or when critical fixes are needed
- **Hotfixes**: As needed for critical issues

## 🏗️ Architecture Decisions

When making significant changes:

1. Discuss in an issue first
2. Consider backward compatibility
3. Document the decision and rationale
4. Update relevant documentation

## 📮 Communication

- **Issues**: Bug reports and feature requests
- **Discussions**: General questions and ideas
- **PRs**: Code contributions
- **Security**: Email maintainers directly

## 🎯 Goals

- Maintain high code quality
- Ensure reliable releases
- Make contributing easy
- Keep users happy

---

Thank you for contributing to Grafana Publisher! 🎉