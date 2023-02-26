"""DataUpdateCoordinator for Supabase Export."""
from __future__ import annotations

from datetime import timedelta
import logging
from random import choices
from string import ascii_letters, digits, punctuation

import async_timeout
from postgrest import APIError as PostgresAPIError, APIResponse as PostgresAPIResponse
from supabase.client import (
    Client as SupabaseClient,
    SupabaseException,
    create_client as create_supabase_client,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_ENTITIES, CONF_URL
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_UPDATE_INTERVAL, DOMAIN
from .data import (
    SupabaseExportCoordinatorData,
    SupabaseExportEntity,
    SupabaseExportMetadata,
)

_LOGGER = logging.getLogger(__name__)


def generate_string(length: int) -> str:
    """Generate a random password."""
    characters = ascii_letters + digits + punctuation
    password = "".join(choices(characters, k=length))

    return password


class SupabaseExportDataUpdateCoordinator(
    DataUpdateCoordinator[SupabaseExportCoordinatorData]
):
    """Class to manage fetching Supabase data from single endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize Supabase coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=DOMAIN,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(
                seconds=entry.options.get(CONF_UPDATE_INTERVAL, 30)
            ),
        )

        self.supabase: SupabaseClient = create_supabase_client(
            entry.data[CONF_URL],
            entry.data[CONF_API_KEY],
        )

        SupabaseExportCoordinatorData.update_forward_refs()

        self.entities: list[str] = entry.options.get(CONF_ENTITIES, [])
        self.supabase_data = SupabaseExportCoordinatorData(
            entities=[],
            metadata=SupabaseExportMetadata(
                id=1,
                provisioned=False,
                url=entry.data[CONF_URL],
            ),
        )
        self.setup = False

    def provision_database(self) -> None:
        """Provision database."""
        self.logger.debug("Provisioning database")
        self.supabase.table("homeassistant_metadata").upsert(
            {
                "id": 1,
                "provisioned": True,
            }
        ).execute()

    def get_metadata(self) -> None:
        """Get metadata."""
        self.logger.debug("Getting metadata")
        response: PostgresAPIResponse = (
            self.supabase.table("homeassistant_metadata").select("*").execute()
        )
        self.logger.debug("Metadata response: %s", response)
        if len(response.data) == 0:
            self.provision_database()
            self.get_metadata()
            return
        self.supabase_data.metadata = SupabaseExportMetadata(
            **response.data[0],
            url=self.supabase_data.metadata.url,
        )
        if not self.supabase_data.metadata.provisioned:
            self.provision_database()
            self.get_metadata()

    def get_entities(self) -> None:
        """Get entities."""
        self.logger.debug("Getting entities")
        response: PostgresAPIResponse = (
            self.supabase.table("homeassistant_entities").select("*").execute()
        )
        self.supabase_data.entities = []
        for entity in response.data:
            self.supabase_data.entities.append(SupabaseExportEntity(**entity))

    def add_entity_data(
        self,
        state: State,
    ) -> None:
        """Add entity data."""
        entity_data = SupabaseExportEntity(
            entity_id=state.entity_id,
            state=str(state.state),
            attributes=state.attributes,
            last_changed=state.last_changed.isoformat(),
        )

        self.logger.debug("Adding entity data: %s", state)
        self.supabase_data.entities.append(entity_data)
        self.supabase.table("homeassistant_entities").insert(
            entity_data.dict(exclude_none=True, exclude_unset=True)
        ).execute()

    def get_and_update_entity(
        self,
        entity_id: str,
    ) -> None:
        """Get and update entity."""
        self.logger.debug("Getting and updating entity: %s", entity_id)
        state = self.hass.states.get(entity_id)
        if state is not None:
            found_items = (
                self.supabase.table("homeassistant_entities")
                .select("*")
                .eq("entity_id", entity_id)
                .execute()
            )
            if len(found_items.data) > 0:
                previous_state = SupabaseExportEntity(**found_items.data[-1])
                if (
                    previous_state.state != str(state.state)
                    and previous_state.last_changed != state.last_changed.isoformat()
                ):
                    self.add_entity_data(state)
            else:
                self.add_entity_data(state)

    async def _async_update_data(self) -> SupabaseExportCoordinatorData:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            async with async_timeout.timeout(20):
                if not self.setup:
                    self.get_metadata()
                    self.get_entities()
                    self.setup = True

                for entity in self.entities:
                    self.get_and_update_entity(entity)
        except (SupabaseException, PostgresAPIError) as err:
            self.logger.warning("Error updating Supabase data: %s", err)
            raise UpdateFailed from err

        return self.supabase_data
