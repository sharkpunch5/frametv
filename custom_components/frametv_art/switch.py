"""Switch entities for Samsung Frame TV Art Mode."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_TV_IP, DOMAIN
from .coordinator import FrameTVCoordinator, FrameTVState


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: FrameTVCoordinator = hass.data[DOMAIN][entry.entry_id]
    tv_ip = entry.data[CONF_TV_IP]

    async_add_entities(
        [
            FrameTVArtModeSwitch(coordinator, tv_ip),
            FrameTVRecoverySwitch(coordinator, tv_ip),
        ]
    )


class FrameTVArtModeSwitch(CoordinatorEntity[FrameTVCoordinator], SwitchEntity):
    """Switch to toggle art mode on/off."""

    _attr_has_entity_name = True
    _attr_name = "Art Mode"
    _attr_icon = "mdi:palette"

    def __init__(self, coordinator: FrameTVCoordinator, tv_ip: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"frametv_{tv_ip}_art_mode"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.art_mode == "on"

    @property
    def available(self) -> bool:
        return (
            self.coordinator.data is not None
            and self.coordinator.data.power is not None
        )

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_art_mode(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_art_mode(False)


class FrameTVRecoverySwitch(CoordinatorEntity[FrameTVCoordinator], SwitchEntity):
    """Switch to enable/disable art mode auto-recovery."""

    _attr_has_entity_name = True
    _attr_name = "Art Recovery"
    _attr_icon = "mdi:autorenew"
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator: FrameTVCoordinator, tv_ip: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"frametv_{tv_ip}_recovery"

    @property
    def is_on(self) -> bool:
        return self.coordinator.recovery_enabled

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.recovery_enabled = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.recovery_enabled = False
        self.async_write_ha_state()
