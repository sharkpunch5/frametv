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
    """Manages WebSocket/REST communication with Samsung Frame TV.

    Keeps persistent connections to avoid repeated pairing popups.
    """

    def __init__(self, host: str, token_file: str | None = None) -> None:
        self.host = host
        self.token_file = token_file or os.path.join(
            os.path.expanduser("~"), ".frametv_token"
        )
        self._art: SamsungTVArt | None = None
        self._remote: SamsungTVWS | None = None

    def _get_art(self) -> SamsungTVArt:
        """Get or create persistent art endpoint connection."""
        if self._art is not None and self._art.is_alive():
            return self._art
        # Close stale connection if any
        if self._art is not None:
            try:
                self._art.close()
            except Exception:
                pass
        self._art = SamsungTVArt(
            host=self.host, port=DEFAULT_PORT, token_file=self.token_file, timeout=5
        )
        return self._art

    def _get_remote(self) -> SamsungTVWS:
        """Get or create persistent remote endpoint connection."""
        if self._remote is not None and self._remote.is_alive():
            return self._remote
        # Close stale connection if any
        if self._remote is not None:
            try:
                self._remote.close()
            except Exception:
                pass
        self._remote = SamsungTVWS(
            host=self.host, port=DEFAULT_PORT, token_file=self.token_file, timeout=5
        )
        return self._remote

    def _close_art(self) -> None:
        """Close art connection (e.g. after error)."""
        if self._art is not None:
            try:
                self._art.close()
            except Exception:
                pass
            self._art = None

    def _close_remote(self) -> None:
        """Close remote connection (e.g. after error)."""
        if self._remote is not None:
            try:
                self._remote.close()
            except Exception:
                pass
            self._remote = None

    def close(self) -> None:
        """Close all connections."""
        self._close_art()
        self._close_remote()

    def ensure_token(self) -> None:
        """Connect to remote endpoint once to obtain token if needed.

        The remote endpoint handles token negotiation (pairing popup).
        The art endpoint does not, so we must get the token here first.
        """
        if self.token_file and os.path.exists(self.token_file):
            try:
                with open(self.token_file) as f:
                    token = f.read().strip()
                if token:
                    return
            except Exception:
                pass
        try:
            _LOGGER.info("No token found, connecting to remote endpoint for pairing")
            remote = self._get_remote()
            remote.send_key("KEY_ENTER")
            _LOGGER.info("Token negotiation complete")
        except Exception as e:
            _LOGGER.debug("Token negotiation: %s", e)
            self._close_remote()

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
        self.ensure_token()
        try:
            art = self._get_art()
            return art.get_artmode()
        except Exception:
            self._close_art()
            return None

    def set_art_mode(self, on: bool) -> bool:
        """Set art mode. Returns True on success."""
        self.ensure_token()
        try:
            art = self._get_art()
            result = art.set_artmode(on)
            status = result.get("status") if isinstance(result, dict) else None
            return status == ("on" if on else "off")
        except Exception as e:
            _LOGGER.warning("set_art_mode failed: %s", e)
            self._close_art()
            return False

    def send_key(self, key: str) -> bool:
        """Send remote key command via persistent connection."""
        try:
            remote = self._get_remote()
            remote.send_key(key)
            return True
        except Exception as e:
            _LOGGER.debug("send_key(%s) failed: %s", key, e)
            self._close_remote()
            return False

    def wake_to_art_mode(self) -> bool:
        """Wake TV from standby and set art mode."""
        _LOGGER.info("Waking TV from standby...")

        if not self.send_key("KEY_POWER"):
            return False

        time.sleep(3)
        self.send_key("KEY_POWER")
        time.sleep(5)

        # After wake, connections are stale — force reconnect
        self._close_art()
        self._close_remote()

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
            art = self._get_art()
            brightness = art.get_brightness()
            return int(brightness) if brightness is not None else None
        except Exception:
            self._close_art()
            return None
