"""Data coordinator for Samsung Frame TV Art Mode."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .tv import FrameTVConnection

_LOGGER = logging.getLogger(__name__)


@dataclass
class FrameTVState:
    """Represents the current state of the Frame TV."""

    power: str | None = None  # "on", "standby", None
    art_mode: str | None = None  # "on", "off", None
    brightness: int | None = None
    model: str | None = None
    name: str | None = None


class FrameTVCoordinator(DataUpdateCoordinator[FrameTVState]):
    """Coordinator that polls TV state and handles art mode recovery + cycling."""

    def __init__(
        self,
        hass: HomeAssistant,
        tv: FrameTVConnection,
        poll_interval: int,
        recovery_cooldown: int,
        art_cycle_minutes: int,
        presence_entity: str | None = None,
    ) -> None:
        from datetime import timedelta

        super().__init__(
            hass,
            _LOGGER,
            name="frametv_art",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.tv = tv
        self.recovery_cooldown = recovery_cooldown
        self.art_cycle_seconds = art_cycle_minutes * 60
        self.presence_entity = presence_entity

        self.prev_power: str | None = None
        self.prev_art: str | None = None
        self.last_recovery_time: float = 0
        self.last_cycle_time: float = 0
        self.art_off_since: float = 0
        self.recovery_enabled: bool = True

    def update_options(
        self,
        poll_interval: int,
        recovery_cooldown: int,
        art_cycle_minutes: int,
        presence_entity: str | None = None,
    ) -> None:
        """Update coordinator options from config entry."""
        from datetime import timedelta

        self.update_interval = timedelta(seconds=poll_interval)
        self.recovery_cooldown = recovery_cooldown
        self.art_cycle_seconds = art_cycle_minutes * 60
        self.presence_entity = presence_entity

    def _is_room_occupied(self) -> bool:
        """Check presence entity if configured."""
        if not self.presence_entity:
            return True  # no sensor = assume occupied
        state = self.hass.states.get(self.presence_entity)
        if state is None:
            return True  # sensor not found = assume occupied
        return state.state == "on"

    async def _async_update_data(self) -> FrameTVState:
        """Poll TV and handle recovery/cycling."""
        state = FrameTVState()

        # Get power state
        state.power = await self.hass.async_add_executor_job(self.tv.get_power_state)

        # Get art mode state
        if state.power == "on":
            state.art_mode = await self.hass.async_add_executor_job(
                self.tv.get_art_mode
            )
        elif state.power == "standby":
            state.art_mode = "off"

        now = time.time()

        # Track when art mode first goes off
        if state.art_mode == "off" and self.prev_art != "off":
            self.art_off_since = now
        elif state.art_mode == "on":
            self.art_off_since = 0

        # Art mode recovery
        if self.recovery_enabled and state.art_mode == "off":
            in_cooldown = (now - self.last_recovery_time) < self.recovery_cooldown
            room_occupied = self._is_room_occupied()

            if not in_cooldown and room_occupied:
                if state.power == "on":
                    if self.art_off_since and (now - self.art_off_since) >= 3:
                        await self._recover_art_mode(state.power)
                elif state.power == "standby":
                    await self._recover_art_mode(state.power)

        # Art cycling
        if (
            self.art_cycle_seconds > 0
            and state.art_mode == "on"
            and state.power == "on"
            and (now - self.last_cycle_time) >= self.art_cycle_seconds
        ):
            await self._cycle_art()

        self.prev_power = state.power
        self.prev_art = state.art_mode

        return state

    async def _recover_art_mode(self, power_state: str) -> None:
        """Attempt to recover art mode."""
        now = time.time()

        if power_state == "on":
            _LOGGER.info("TV on but art mode off — recovering")
            success = await self.hass.async_add_executor_job(self.tv.set_art_mode, True)
            if success:
                _LOGGER.info("Art mode recovery: SUCCESS")
                self.last_recovery_time = now
            else:
                _LOGGER.warning("Art mode recovery: FAILED")

        elif power_state == "standby":
            _LOGGER.info("TV in standby — waking to art mode")
            success = await self.hass.async_add_executor_job(self.tv.wake_to_art_mode)
            if success:
                self.last_recovery_time = now

    async def _cycle_art(self) -> None:
        """Cycle to next artwork."""
        success = await self.hass.async_add_executor_job(self.tv.send_key, "KEY_RIGHT")
        if success:
            self.last_cycle_time = time.time()
            _LOGGER.info("Cycled art (KEY_RIGHT)")

    async def async_set_art_mode(self, on: bool) -> None:
        """Set art mode on/off."""
        await self.hass.async_add_executor_job(self.tv.set_art_mode, on)
        await self.async_request_refresh()

    async def async_cycle_art(self) -> None:
        """Manually cycle to next artwork."""
        await self._cycle_art()
        await self.async_request_refresh()
