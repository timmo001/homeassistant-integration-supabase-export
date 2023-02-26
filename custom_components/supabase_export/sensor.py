"""Support for Supabase Export sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .coordinator import SupabaseExportDataUpdateCoordinator
from .entity import SupabaseExportEntity


@dataclass
class SupabaseExportSensorEntityDescription(SensorEntityDescription):
    """Class describing Supabase sensor entities."""

    value: Callable = round


SENSOR_TYPES: tuple[SupabaseExportSensorEntityDescription, ...] = (
    SupabaseExportSensorEntityDescription(
        key="entity_records",
        name="Entity Records",
        icon="mdi:counter",
        value=lambda data: len(data.entities),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Supabase sensor based on a config entry."""
    coordinator: SupabaseExportDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for description in SENSOR_TYPES:
        entities.append(
            SupabaseExportSensor(
                coordinator,
                description,
            )
        )

    async_add_entities(entities)


class SupabaseExportSensor(SupabaseExportEntity, SensorEntity):
    """Define a Supabase sensor."""

    entity_description: SupabaseExportSensorEntityDescription

    def __init__(
        self,
        coordinator: SupabaseExportDataUpdateCoordinator,
        description: SupabaseExportSensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = description

    @property
    def native_value(self) -> StateType:
        """Return the state."""
        try:
            return cast(StateType, self.entity_description.value(self.coordinator.data))
        except TypeError:
            return None
