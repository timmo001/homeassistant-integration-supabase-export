"""Entity for Supabase Export."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SupabaseExportDataUpdateCoordinator


class SupabaseExportEntity(CoordinatorEntity[SupabaseExportDataUpdateCoordinator]):
    """Defines a base Supabase entity."""

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Supabase instance."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data.metadata.url)},
            name=self.coordinator.data.metadata.url,
        )

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this entity."""
        return f"{DOMAIN}_{self.coordinator.data.metadata.url}_{self.entity_description.key}"
