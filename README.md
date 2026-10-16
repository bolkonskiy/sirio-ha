# Sirio Universal

Custom integration for **Sirio / WinET** pump controllers with the universal onboard web interface (`/ajax/get-registers`).

All entities are grouped under a single device. Supports multiple controllers via separate config entries.

## Features

- Sensors: pressure, voltage, current, frequency, temperature, IGBT temperature, set pressure, starts, hours, error code, power
- Binary sensors: running, error, pump enabled, soft start
- Switches: pump, soft start
- Config flow: add controller by IP/hostname
- Options: polling interval, auto soft-start

## Installation

### HACS (recommended)

1. Add this repository as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/) (Integration).
2. Install **Sirio Universal** from HACS.
3. Restart Home Assistant.
4. **Settings → Devices & services → Add integration → Sirio Universal**
5. Enter controller IP, e.g. `192.168.1.82`.

### Manual

Copy `custom_components/sirio` to your Home Assistant `config/custom_components/` directory and restart HA.

## Migration from YAML package

If you used `packages/sirio_pump.yaml`:

1. Install this integration and add the controller.
2. Assign the device to the **Котельная** area.
3. Disable or remove `sirio_pump.yaml` from packages.
4. Update automations/dashboards to new entity IDs (shown under the Sirio device).

## Development

Universal WinET REST API — works with any controller using the same register map (`key=001` status payload).

## License

MIT

Репозиторий: https://git.chprkv.by/anton/sirio-universal
