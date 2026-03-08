"""Samsung Frame TV Art Mode integration."""

from __future__ import annotations

import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

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
from .coordinator import FrameTVCoordinator
from .tv import FrameTVConnection

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Frame TV Art Mode from a config entry."""
    tv_ip = entry.data[CONF_TV_IP]

    token_dir = hass.config.path(".storage")
    token_file = os.path.join(token_dir, f"frametv_art_{tv_ip.replace('.', '_')}_token")

    tv = FrameTVConnection(host=tv_ip, token_file=token_file)

    def _get(key, default):
        return entry.options.get(key, entry.data.get(key, default))

    coordinator = FrameTVCoordinator(
        hass,
        tv=tv,
        poll_interval=_get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
        recovery_cooldown=_get(CONF_RECOVERY_COOLDOWN, DEFAULT_RECOVERY_COOLDOWN),
        art_cycle_minutes=_get(CONF_ART_CYCLE_MINUTES, DEFAULT_ART_CYCLE_MINUTES),
        presence_entity=_get(CONF_PRESENCE_ENTITY, None) or None,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    return True


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: FrameTVCoordinator = hass.data[DOMAIN][entry.entry_id]

    def _get(key, default):
        return entry.options.get(key, entry.data.get(key, default))

    coordinator.update_options(
        poll_interval=_get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
        recovery_cooldown=_get(CONF_RECOVERY_COOLDOWN, DEFAULT_RECOVERY_COOLDOWN),
        art_cycle_minutes=_get(CONF_ART_CYCLE_MINUTES, DEFAULT_ART_CYCLE_MINUTES),
        presence_entity=_get(CONF_PRESENCE_ENTITY, None) or None,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
