# Home Assistant IntesisHome Local Integration
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

[![HACS Action](https://github.com/donfrensis/HA-IntesisHome-Local/actions/workflows/HACS.yaml/badge.svg)](https://github.com/donfrensis/HA-IntesisHome-Local/actions/workflows/hacs.yaml)
[![hassfest](https://github.com/donfrensis/HA-IntesisHome-Local/actions/workflows/hassfest_validation.yaml/badge.svg)](https://github.com/donfrensis/HA-IntesisHome-Local/actions/workflows/hassfest_validation.yaml)
[![release](https://img.shields.io/github/v/release/donfrensis/HA-IntesisHome-Local.svg)](https://github.com/donfrensis/HA-IntesisHome-Local/releases)
Simplified fork of the IntesisHome integration for Home Assistant

*This project is a simplified fork of the original IntesisHome integration by @jnimmo. The original version supported various Intesis devices, while this fork focuses exclusively on local HTTP control for selected devices.*

This custom version exclusively supports local control via HTTP for selected devices.

## Features
- Full climate control (temperature, modes, fan speeds)
- Real-time state updates
- Connectivity monitoring for each device
- Modern UI-based configuration
- No cloud connection required
- No YAML configuration needed

## Changes from Original Version
- Focuses only on local HTTP control
- Updates code to resolve deprecated method warnings
- Fixes climate entity feature handling
- Improves async operations handling
- Removes unused device types and related code

## Installation

### HACS Installation
1. Open HACS in your Home Assistant instance
2. Click on the 3 dots in the top right corner
3. Select "Custom repositories"
4. Add the URL of this repository
5. Select "Integration" as the category
6. Click "Add"
7. Install the integration through HACS
8. Restart Home Assistant

### Manual Installation
1. Download the latest release
2. Copy the `custom_components/intesishome` folder to your `custom_components` directory
3. Restart Home Assistant

## Setup
1. Go to Settings -> Devices & Services
2. Click "+ ADD INTEGRATION"
3. Search for "IntesisHome Local"
4. Follow the configuration steps

## Supported Devices
Local HTTP Control (intesishome_local):

| Device                  | HTTP - intesishome_local | 
| ----------------------- |:-------------------------| 
| TO-RC-WIFI-1B          | :white_check_mark:       |

### Supported Features
Each device provides:
- Climate entity with full control capabilities
- Binary sensor showing device connectivity status
- Real-time state updates
- Modern UI-based configuration

## Important Notes
If you are using the original version of the integration, completely remove it before installing this version. The two versions cannot coexist on the same system.

## Credits and Support
This integration is based on the excellent work done by @jnimmo on the original [IntesisHome Integration](https://github.com/jnimmo/hass-intesishome). 

If you'd like to show appreciation for the original work:
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jnimmo) (@jnimmo)

For issues specific to this simplified local-only version, please use this repository's issue tracker.

## License
MIT License