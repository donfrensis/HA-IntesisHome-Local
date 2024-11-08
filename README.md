# Home Assistant IntesisHome Local Integration
Simplified fork of the IntesisHome integration for Home Assistant

*This project is a simplified fork of the original IntesisHome integration by @jnimmo. The original version supported various Intesis devices, while this fork focuses exclusively on local HTTP control for selected devices.*

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

This custom version exclusively supports local control via HTTP for selected devices.

## Changes from Original Version
- Focuses only on local HTTP control
- Updates code to resolve deprecated method warnings
- Fixes climate entity feature handling
- Improves async operations handling
- Removes unused device types and related code

## Supported Devices
Local HTTP Control (intesishome_local):

| Device                  | HTTP - intesishome_local | 
| ----------------------- |:-------------------------| 
| TO-RC-WIFI-1B          | :white_check_mark:       |

## Setup
1. Add this custom repository to HACS, or manually download the files into your custom_components directory
2. Restart Home Assistant
3. [![Start IntesisHome configuration in Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=intesishome) or navigate to integrations and add the IntesisHome integration through the user interface
4. Provide the required details for your device (IP address, username, password)

### Supported Features
- Full climate control (temperature, modes, fan speeds)
- Real-time state updates
- Modern UI-based configuration
- No cloud connection required
- No YAML configuration needed

## Important Notes
If you are using the original version of the integration, completely remove it before installing this version. The two versions cannot coexist on the same system.

## Credits and Support
This integration is based on the excellent work done by @jnimmo on the original [IntesisHome Integration](https://github.com/jnimmo/hass-intesishome). 

If you'd like to show appreciation for the original work:
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jnimmo) (@jnimmo)

For issues specific to this simplified local-only version, please use this repository's issue tracker.
