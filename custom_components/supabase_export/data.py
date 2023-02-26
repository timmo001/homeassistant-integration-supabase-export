"""Data classes for Supabase Export."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel  # pylint: disable=no-name-in-module


class SupabaseExportCoordinatorData(BaseModel):
    """Supabase Coordianator Data."""

    entities: list[SupabaseExportEntity] = []
    metadata: SupabaseExportMetadata


class SupabaseExportEntity(BaseModel):
    """Supabase Entities."""

    id: int | None = None
    created_at: str | None = None
    entity_id: str
    state: str | None = None
    attributes: dict[str, Any] | None = None
    last_changed: str | None = None


class SupabaseExportMetadata(BaseModel):
    """Supabase Metadata."""

    id: int
    created_at: str | None = None
    provisioned: bool
    url: str
