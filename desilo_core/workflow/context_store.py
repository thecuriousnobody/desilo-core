"""
Filesystem-based StartupContextStore

Default implementation using JSON files for development and testing.
White-label implementations replace this with database-backed stores
(Supabase, Postgres, etc.)
"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

from desilo_core.contracts.workflow import StartupContextStore, StartupContext


class FileContextStore(StartupContextStore):
    """JSON file-based context store.

    Stores one file per startup idea under:
        {storage_dir}/{user_id}/{startup_id}.json

    Args:
        storage_dir: Root directory for storing startup contexts.
    """

    def __init__(self, storage_dir: str = "./startup-contexts"):
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    async def get_user_startups(self, user_id: str) -> List[StartupContext]:
        user_dir = self._dir / user_id
        if not user_dir.exists():
            return []

        contexts = []
        for filepath in user_dir.glob("*.json"):
            data = json.loads(filepath.read_text())
            contexts.append(self._from_dict(data))

        # Most recently accessed first
        contexts.sort(
            key=lambda c: c.last_accessed or c.created_at or datetime.min,
            reverse=True
        )
        return contexts

    async def get_startup_by_id(self, startup_id: str) -> Optional[StartupContext]:
        for filepath in self._dir.rglob(f"{startup_id}.json"):
            data = json.loads(filepath.read_text())
            return self._from_dict(data)
        return None

    async def save_startup(self, context: StartupContext) -> str:
        user_dir = self._dir / context.user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        if not context.created_at:
            context.created_at = datetime.now(timezone.utc)
        context.last_accessed = datetime.now(timezone.utc)

        filepath = user_dir / f"{context.id}.json"
        filepath.write_text(json.dumps(self._to_dict(context), indent=2, default=str))
        return context.id

    def _to_dict(self, ctx: StartupContext) -> dict:
        return {
            "id": ctx.id,
            "user_id": ctx.user_id,
            "name": ctx.name,
            "description": ctx.description,
            "industry": ctx.industry,
            "search_terms": ctx.search_terms,
            "geographical_scope": ctx.geographical_scope,
            "created_at": ctx.created_at.isoformat() if ctx.created_at else None,
            "last_accessed": ctx.last_accessed.isoformat() if ctx.last_accessed else None,
            "metadata": ctx.metadata,
        }

    def _from_dict(self, data: dict) -> StartupContext:
        created = data.get("created_at")
        accessed = data.get("last_accessed")
        return StartupContext(
            id=data["id"],
            user_id=data["user_id"],
            name=data["name"],
            description=data["description"],
            industry=data.get("industry"),
            search_terms=data.get("search_terms"),
            geographical_scope=data.get("geographical_scope"),
            created_at=datetime.fromisoformat(created) if created else None,
            last_accessed=datetime.fromisoformat(accessed) if accessed else None,
            metadata=data.get("metadata"),
        )
