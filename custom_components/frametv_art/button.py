"""Button entities for Samsung Frame TV Art Mode."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_TV_IP, DOMAIN
from .coordinator import FrameTVCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: FrameTVCoordinator = hass.data[DOMAIN][entry.entry_id]
    tv_ip = entry.data[CONF_TV_IP]

    async_add_entities(
        [
            FrameTVNextArtButton(coordinator, tv_ip),
        ]
    )


class FrameTVNextArtButton(CoordinatorEntity[FrameTVCoordinator], ButtonEntity):
    """Button to cycle to next artwork."""

    _attr_has_entity_name = True
    _attr_name = "Next Artwork"
    _attr_icon = "mdi:skip-next"

    def __init__(self, coordinator: FrameTVCoordinator, tv_ip: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"frametv_{tv_ip}_next_art"

    async def async_press(self) -> None:
        await self.coordinator.async_cycle_art()
