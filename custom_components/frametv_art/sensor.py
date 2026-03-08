"""Sensor entities for Samsung Frame TV Art Mode."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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
            FrameTVStateSensor(coordinator, tv_ip),
        ]
    )


class FrameTVStateSensor(CoordinatorEntity[FrameTVCoordinator], SensorEntity):
    """Sensor showing the combined TV state."""

    _attr_has_entity_name = True
    _attr_name = "State"
    _attr_icon = "mdi:television"

    def __init__(self, coordinator: FrameTVCoordinator, tv_ip: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"frametv_{tv_ip}_state"

    @property
    def native_value(self) -> str | None:
        if self.coordinator.data is None:
            return None
        power = self.coordinator.data.power
        art = self.coordinator.data.art_mode
        if power is None:
            return "unavailable"
        if power == "standby":
            return "standby"
        if art == "on":
            return "art_mode"
        return "on"

    @property
    def extra_state_attributes(self) -> dict:
        if self.coordinator.data is None:
            return {}
        return {
            "power_state": self.coordinator.data.power,
            "art_mode": self.coordinator.data.art_mode,
            "recovery_enabled": self.coordinator.recovery_enabled,
        }
