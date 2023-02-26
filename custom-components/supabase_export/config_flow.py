"""Config flow for Supabase Export integration."""
from __future__ import annotations

import logging
from typing import Any

from supabase.client import (
    Client as SupabaseClient,
    SupabaseException,
    create_client as create_supabase_client,
)
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_ENTITIES, CONF_URL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import CONF_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_API_KEY): str,
    }
)


# SQL to create the tables:
#
# create table homeassistant_entities (
#   id bigint not null primary key,
#   created_at timestamp default now(),
#   entity_id text not null,
#   state text,
#   attributes json,
#   last_changed timestamp default now()
# );
#
# create table homeassistant_metadata (
#   id bigint not null primary key,
#   created_at timestamp default now(),
#   provisioned boolean,
#   data json
# );


async def validate_input(data: dict[str, str]) -> dict[str, Any]:
    """Validate the user input allows us to connect to Supabase.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    try:
        supabase: SupabaseClient = create_supabase_client(
            data[CONF_URL],
            data[CONF_API_KEY],
        )
    except SupabaseException as err:
        _LOGGER.warning("Supabase error: %s", err)
        raise CannotConnect from err

    return {"title": supabase.supabase_url}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Supabase Export."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, str] | None = None,
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_URL])
            self._abort_if_unique_id_configured()
            try:
                info = await validate_input(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Supbabase Export."""

    def __init__(
        self,
        config_entry: config_entries.ConfigEntry,
    ) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(CONF_UPDATE_INTERVAL, 30),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=30, max=86400),
                    ),
                    vol.Required(
                        CONF_ENTITIES,
                        default=self.config_entry.options.get(CONF_ENTITIES, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            multiple=True,
                        ),
                    ),
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
