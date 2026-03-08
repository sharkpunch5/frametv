"""Samsung Frame TV connection wrapper."""

from __future__ import annotations

import logging
import os
import time
import urllib3

from samsungtvws import SamsungTVWS
from samsungtvws.art import SamsungTVArt

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 8002


class FrameTVConnection:
    """Manages WebSocket/REST communication with Samsung Frame TV."""

    def __init__(self, host: str, token_file: str | None = None) -> None:
        self.host = host
        self.token_file = token_file or os.path.join(
            os.path.expanduser("~"), ".frametv_token"
        )

    def get_power_state(self) -> str | None:
        """Get TV power state via REST API. Returns 'on', 'standby', or None."""
        try:
            tv = SamsungTVWS(host=self.host, port=DEFAULT_PORT, token_file=self.token_file)
            info = tv.rest_device_info()
            return info.get("device", {}).get("PowerState")
        except Exception:
            return None

    def get_device_info(self) -> dict | None:
        """Get device info via REST API."""
        try:
            tv = SamsungTVWS(host=self.host, port=DEFAULT_PORT, token_file=self.token_file)
            info = tv.rest_device_info()
            return info.get("device", {})
        except Exception:
            return None

    def get_art_mode(self) -> str | None:
        """Get art mode state. Returns 'on', 'off', or None."""
        try:
            art = SamsungTVArt(
                host=self.host, port=DEFAULT_PORT, token_file=self.token_file, timeout=3
            )
            state = art.get_artmode()
            art.close()
            return state
        except Exception:
            return None

    def set_art_mode(self, on: bool) -> bool:
        """Set art mode. Returns True on success."""
        try:
            art = SamsungTVArt(
                host=self.host, port=DEFAULT_PORT, token_file=self.token_file, timeout=5
            )
            result = art.set_artmode(on)
            art.close()
            status = result.get("status") if isinstance(result, dict) else None
            return status == ("on" if on else "off")
        except Exception as e:
            _LOGGER.warning("set_art_mode failed: %s", e)
            return False

    def send_key(self, key: str) -> bool:
        """Send remote key command."""
        try:
            tv = SamsungTVWS(
                host=self.host, port=DEFAULT_PORT, token_file=self.token_file, timeout=5
            )
            tv.send_key(key)
            return True
        except Exception as e:
            _LOGGER.warning("send_key(%s) failed: %s", key, e)
            return False

    def wake_to_art_mode(self) -> bool:
        """Wake TV from standby and set art mode."""
        _LOGGER.info("Waking TV from standby...")

        if not self.send_key("KEY_POWER"):
            return False

        time.sleep(3)
        self.send_key("KEY_POWER")
        time.sleep(5)

        for _attempt in range(3):
            art_state = self.get_art_mode()
            if art_state is not None:
                _LOGGER.info("Art API ready (state=%s), setting art mode", art_state)
                if self.set_art_mode(True):
                    _LOGGER.info("Wake to art mode: SUCCESS")
                    return True
            time.sleep(3)

        _LOGGER.warning("Wake to art mode: FAILED after retries")
        return False

    def get_brightness(self) -> int | None:
        """Get art mode brightness (0-10)."""
        try:
            art = SamsungTVArt(
                host=self.host, port=DEFAULT_PORT, token_file=self.token_file, timeout=5
            )
            brightness = art.get_brightness()
            art.close()
            return int(brightness) if brightness is not None else None
        except Exception:
            return None
