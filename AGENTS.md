# Coding Agent Standards — DeSilo Core

How we use AI coding agents when working on the core library. This is a shared, generic package — extra care is required since changes affect all downstream white-label implementations.

---

## Setup

### Claude Code

```bash
# Install
npm install -g @anthropic-ai/claude-code

# Or native installer (macOS/Linux)
curl -fsSL https://claude.ai/install.sh | bash

# Launch in this project
cd /path/to/desilo-core
claude
```

Claude reads `CLAUDE.md` automatically when it starts in the project directory.

### Python Environment

```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in editable mode with dev deps
pip install -e ".[dev]"
```

### Testing Against desilo-distillery Locally

When you change something in core, test it against the distillery app without pushing:

```bash
# In the distillery backend's venv
cd /path/to/desilo-distillery/railway-backend
source venv/bin/activate

# Install your local core (overrides the GitHub version)
pip install -e /path/to/desilo-core

# Start the backend — it now uses your local core changes
python main.py
```

Any edits to desilo-core files are reflected immediately (that's what `-e` does). No reinstall needed between changes.

**Note:** Running `pip install -r requirements.txt` in distillery will reinstall core from GitHub and overwrite your local link. Just re-run `pip install -e /path/to/desilo-core` to switch back.

---

## Rules for This Repo

### 1. The Austin Test — Non-Negotiable

Every file must be usable by any organization anywhere. Before committing, run:

```bash
grep -rE "Distillery|Peoria|Sarah|Central Illinois" desilo_core/
```

**Zero matches.** If your code references anything partner-specific, it belongs in desilo-distillery, not here.

### 2. Contracts Are Stable

The ABCs in `desilo_core/contracts/` are a public API that downstream packages depend on.

**Safe changes:**
- Adding a new method with a default implementation
- Adding a new contract class
- Fixing bugs in default method implementations

**Breaking changes (require major version bump + team discussion):**
- Changing an abstract method signature
- Removing an abstract method
- Renaming a contract class
- Changing the inheritance hierarchy

Always tell Claude about this constraint:
> "The contracts in contracts/ are stable APIs. Don't change existing abstract method signatures."

### 3. Write Tests

This library has `pytest` configured. Every new feature or bug fix should include tests:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_contracts.py
```

Tests go in a `tests/` directory at the repo root. Mirror the package structure:
```
tests/
├── test_contracts/
│   ├── test_agent.py
│   ├── test_search.py
│   └── ...
├── test_agents/
│   ├── test_base_research_crew.py
│   └── ...
└── test_memory/
    └── test_collaborative_memory.py
```

### 4. Keep Dependencies Minimal

This is a library, not an application. Every dependency you add becomes a dependency for all downstream consumers. Before adding a new package:
- Is it already covered by an existing dependency?
- Can the functionality be achieved with the standard library?
- Is it a well-maintained, stable package?

Update `pyproject.toml` for any new dependencies — not a requirements.txt.

---

## Workflow Standards

### Branch First

```bash
git checkout -b feat/your-feature-name
# Work with Claude
# Push and create a PR
```

### Git Conventions

```
feat/short-description     — New features
fix/short-description      — Bug fixes
chore/short-description    — Maintenance, config, docs
```

Commit messages:
```
feat: Add SerperSearchAdapter implementation
fix: Handle empty results in BaseResearchCrew
chore: Update pytest config for async tests
```

### Review AI-Generated Code

Before committing, check:
- [ ] Does it pass the Austin Test? (no partner-specific references)
- [ ] Does it maintain contract stability? (no broken ABCs)
- [ ] Are there tests for the change?
- [ ] Are the imports clean? (no unnecessary new dependencies)
- [ ] Does it follow existing patterns in the codebase?

### Version Bumps

When making changes, update `__version__` in `desilo_core/__init__.py` and `version` in `pyproject.toml`:
- **Patch** (0.1.0 → 0.1.1): Bug fixes, docs, non-breaking tweaks
- **Minor** (0.1.0 → 0.2.0): New features, new contracts, new adapters
- **Major** (0.1.0 → 1.0.0): Breaking changes to contracts or public API

---

## Common Claude Code Commands

| Command | What It Does |
|---------|-------------|
| `claude` | Start interactive session |
| `claude "task"` | One-shot task |
| `claude -c` | Continue last conversation |
| `/help` | Show available commands |

### Useful Patterns

```bash
# Quick Austin Test
claude "run the Austin Test — grep for any partner-specific references in desilo_core/"

# Explore contracts
claude "explain how AgentPersona is implemented and what methods a white label needs to provide"

# Add a new adapter
claude "add a SerperSearchAdapter in desilo_core/adapters/ that implements the SearchAdapter contract"
```

---

## What NOT to Do

- **Don't add partner-specific code** — that's what desilo-distillery is for
- **Don't break contract signatures** — downstream packages depend on them
- **Don't add heavy dependencies** — keep the library lightweight
- **Don't skip tests** — this is shared infrastructure, it needs to be reliable
- **Don't push directly to main** — use branches and PRs
- **Don't forget to test against distillery** — `pip install -e` and verify the app still works
