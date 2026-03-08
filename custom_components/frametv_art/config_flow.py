"""Config flow for Samsung Frame TV Art Mode."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ART_CYCLE_MINUTES,
    CONF_POLL_INTERVAL,
    CONF_PRESENCE_ENTITY,
    CONF_RECOVERY_COOLDOWN,
    CONF_TV_IP,
    DEFAULT_ART_CYCLE_MINUTES,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_RECOVERY_COOLDOWN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class FrameTVArtConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Frame TV Art Mode."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            tv_ip = user_input[CONF_TV_IP]

            # Check not already configured
            await self.async_set_unique_id(tv_ip)
            self._abort_if_unique_id_configured()

            # Test connection
            try:
                from samsungtvws import SamsungTVWS

                tv = await self.hass.async_add_executor_job(
                    lambda: SamsungTVWS(host=tv_ip, port=8002, timeout=5)
                )
                info = await self.hass.async_add_executor_job(tv.rest_device_info)
                device = info.get("device", {})
                if not device.get("FrameTVSupport") == "true":
                    errors["base"] = "not_frame_tv"
                else:
                    name = device.get("name", "Frame TV")
                    return self.async_create_entry(title=name, data=user_input)
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TV_IP): str,
                    vol.Optional(
                        CONF_ART_CYCLE_MINUTES, default=DEFAULT_ART_CYCLE_MINUTES
                    ): vol.All(int, vol.Range(min=0, max=60)),
                    vol.Optional(
                        CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL
                    ): vol.All(int, vol.Range(min=5, max=60)),
                    vol.Optional(
                        CONF_RECOVERY_COOLDOWN, default=DEFAULT_RECOVERY_COOLDOWN
                    ): vol.All(int, vol.Range(min=10, max=300)),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> FrameTVArtOptionsFlow:
        return FrameTVArtOptionsFlow(config_entry)


class FrameTVArtOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Frame TV Art Mode."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ART_CYCLE_MINUTES,
                        default=self.config_entry.options.get(
                            CONF_ART_CYCLE_MINUTES,
                            self.config_entry.data.get(
                                CONF_ART_CYCLE_MINUTES, DEFAULT_ART_CYCLE_MINUTES
                            ),
                        ),
                    ): vol.All(int, vol.Range(min=0, max=60)),
                    vol.Optional(
                        CONF_POLL_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_POLL_INTERVAL,
                            self.config_entry.data.get(
                                CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
                            ),
                        ),
                    ): vol.All(int, vol.Range(min=5, max=60)),
                    vol.Optional(
                        CONF_RECOVERY_COOLDOWN,
                        default=self.config_entry.options.get(
                            CONF_RECOVERY_COOLDOWN,
                            self.config_entry.data.get(
                                CONF_RECOVERY_COOLDOWN, DEFAULT_RECOVERY_COOLDOWN
                            ),
                        ),
                    ): vol.All(int, vol.Range(min=10, max=300)),
                    vol.Optional(
                        CONF_PRESENCE_ENTITY,
                        default=self.config_entry.options.get(
                            CONF_PRESENCE_ENTITY, ""
                        ),
                    ): str,
                }
            ),
        )
