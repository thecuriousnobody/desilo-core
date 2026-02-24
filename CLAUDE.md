# DeSilo Core - AI Context

Open-source startup intelligence engine. Generic infrastructure for AI-powered startup platforms.

## Architecture

```
desilo-core/
├── desilo_core/           # Main package (pip installable)
│   ├── contracts/         # STABLE ABCs — do not break without major version bump
│   │   ├── agent.py       # AgentPersona — conversational AI personality interface
│   │   ├── search.py      # SearchAdapter — pluggable search sources
│   │   ├── resources.py   # ResourceConnector — regional resource databases
│   │   ├── knowledge.py   # KnowledgeBase — proprietary knowledge integration
│   │   └── tenant.py      # TenantConfig — multi-tenant configuration schema
│   ├── agents/            # Generic CrewAI patterns
│   │   ├── base_research_crew.py  # Foundation for research agent teams
│   │   └── simple_market_crew.py  # 4-agent market analysis pattern
│   ├── memory/            # Memory systems
│   │   └── collaborative_memory.py  # AI-human interaction memory
│   ├── adapters/          # Built-in adapter implementations (placeholder)
│   └── api/               # FastAPI framework (placeholder)
├── config/
│   └── industries.yaml    # Generic industry taxonomy (50+ industries)
├── ui/                    # React components (placeholder)
├── pyproject.toml         # Package metadata, dependencies
└── README.md
```

## Key Concepts

### Contracts Are Stable

The contracts in `desilo_core/contracts/` are abstract base classes (ABCs) that white-label implementations depend on. They are marked **STABLE**:
- Do not change method signatures without a major version bump
- Do not remove existing abstract methods
- Adding new optional methods (with default implementations) is safe

### The Austin Test

Every file must pass:
> If someone at a random accelerator in Austin, Texas could use this module with zero modification, it belongs here.

**No references to**: Distillery, Peoria, Sarah Martinez, Central Illinois, or any partner-specific content. Verify with:
```bash
grep -rE "Distillery|Peoria|Sarah|Central Illinois" desilo_core/
```
Zero matches required.

### How White Labels Use This

```python
# White label implements the contracts
from desilo_core.contracts import AgentPersona, PersonaConfig

class SarahMartinez(AgentPersona):
    def get_config(self) -> PersonaConfig:
        return PersonaConfig(name="Sarah", role="Intake Specialist", ...)
```

The primary consumer is [desilo-distillery](https://github.com/thecuriousnobody/desilo-distillery), which installs this package via pip.

## Dependencies

- `crewai>=0.28.0` — multi-agent orchestration
- `crewai-tools>=0.2.0` — built-in CrewAI tools
- `pydantic>=2.0.0` — data validation
- `python-dotenv>=1.0.0` — environment management

Dev: `pytest>=7.0.0`, `pytest-asyncio>=0.21.0`

## Development

```bash
# Install in editable mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run Austin Test check
grep -rE "Distillery|Peoria|Sarah|Central Illinois" desilo_core/
```

## Current State

- **Version**: 0.1.0 (Alpha)
- **Python**: 3.10+
- **License**: MIT
- **Phase 1 (Foundation)**: Complete — contracts, base crews, memory, config
- **Phase 2 (Infrastructure)**: Pending — generic FastAPI app, search adapters, MCP server, UI components
- **Phase 3 (Multi-Tenancy)**: Pending — tenant middleware, DB isolation, config system

## Downstream Impact

Changes to this package affect `desilo-distillery` (and future white labels). The distillery's `requirements.txt` installs this from GitHub:
```
desilo-core @ git+https://github.com/thecuriousnobody/desilo-core.git@main
```

For local development against distillery:
```bash
cd /path/to/desilo-distillery/railway-backend
pip install -e /path/to/desilo-core
```
