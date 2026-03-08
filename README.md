# Samsung Frame TV Art Mode

A Home Assistant custom integration for Samsung Frame TV that automatically manages art mode. Built for the 2024 Frame TV but should work with other Frame TV models.

## Features

- **Art mode auto-recovery** — When an external device (e.g. Apple TV remote) turns off the TV instead of returning to art mode, the integration detects this and automatically restores art mode
- **Art cycling** — Periodically cycles to the next artwork using the TV's own rotation logic, supporting Art Store subscriptions, favourites, and endless stream mode
- **Presence-aware** — Optionally uses a presence/motion sensor to only recover art mode when the room is occupied. If the room is empty, the TV stays off to save power
- **Manual controls** — Art mode switch, recovery toggle, and "next artwork" button in the HA dashboard

## How It Works

The integration communicates with the Frame TV via the local WebSocket API (`samsung-tv-ws-api`) and REST API:

| TV State | PowerState | Art Mode | Integration Action |
|----------|-----------|----------|-------------------|
| Displaying art | `on` | `on` | No action |
| External device turned off | `on` | `off` | `set_artmode(True)` |
| Hard standby | `standby` | — | `KEY_POWER` wake + `set_artmode(True)` |

Art cycling uses `KEY_RIGHT` which lets the TV handle artwork selection natively — this respects your Art Store subscription, endless stream mode, and favourites.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add this repository URL with category **Integration**
4. Search for "Samsung Frame TV Art Mode" and install
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/frametv_art` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Samsung Frame TV Art Mode"
3. Enter your TV's IP address
4. **Check your TV** — you may need to approve a pairing popup on the TV screen
5. Configure options:
   - **Art cycle interval** — minutes between artwork changes (0 = disabled, default: 5)
   - **Poll interval** — seconds between state checks (default: 10)
   - **Recovery cooldown** — minimum seconds between recovery attempts (default: 30)

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| `switch.frame_tv_art_mode` | Switch | Toggle art mode on/off |
| `switch.frame_tv_art_recovery` | Switch | Enable/disable auto-recovery |
| `sensor.frame_tv_state` | Sensor | Combined state: `art_mode`, `on`, `standby`, `unavailable` |
| `button.frame_tv_next_artwork` | Button | Skip to next artwork |

## Options

After setup, go to the integration options to configure:

- **Presence sensor entity** — optional `binary_sensor` entity ID for room occupancy. When configured, art mode only recovers when the room is occupied. Works well with mmWave presence sensors.

## Notes

### First-time pairing

The TV will show a pairing popup the first time the integration connects. You need to approve it on the TV screen. The token is saved automatically for future connections.

### Apple TV / CEC

The Samsung Frame TV 2024 has a known issue where external remotes (e.g. Apple TV) trigger a hard power-off instead of returning to art mode. Disabling CEC doesn't fully resolve this. This integration works around the issue by detecting the state change and automatically recovering art mode.

### Network

The TV should have a static IP or DHCP reservation. The integration communicates locally — no cloud dependency.

## Requirements

- Samsung Frame TV (tested on 2024 model QA55LS03DA)
- TV and Home Assistant on the same network
- TV IP address (static or reserved)
