# DeSilo Core

**Generic Startup Intelligence Engine**

This is the open-source core of the DeSilo platform. It provides the foundational infrastructure for building AI-powered startup intelligence systems.

## What's Included

- **Contracts**: Interface definitions (Python ABCs) that white-label implementations must follow
- **Agents**: Generic CrewAI agent patterns for market research, topic analysis, etc.
- **Adapters**: Pluggable adapters for search, LLMs, storage, etc.
- **Memory**: Collaborative memory systems for AI-human interaction
- **UI Components**: Themeable React components (no branding)
- **Config**: Generic configuration schemas

## What's NOT Included

This core does NOT contain:
- Partner-specific personas
- Regional data (partner-specific resource databases)
- Proprietary knowledge bases
- Partner branding

Those belong in white-label implementations that import from this core.

## Usage

```python
from desilo_core.contracts import AgentPersona, SearchAdapter
from desilo_core.agents import BaseResearchCrew
from desilo_core.memory import CollaborativeMemory

# Implement the contracts for your organization
class MyPersona(AgentPersona):
    def get_backstory(self) -> str:
        return "Your custom persona backstory..."

# Use the generic infrastructure
crew = BaseResearchCrew(persona=MyPersona())
```

## The Austin Test

Every file in this repository passes the "Austin Test":

> If someone at a random accelerator in Austin, Texas could use this module with zero modification, it belongs here.

## Contributing

Before adding any file, run:
```bash
# Replace with your organization's proprietary terms
grep -E "YourOrgName|YourCity|YourPersona" <file>
```

**Zero matches required.**

## License

MIT (or Apache 2.0 - TBD)
