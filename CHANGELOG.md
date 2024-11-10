# Changelog

## [1.1.5] - 2024-11-10
### Fixed
- Fixed device connectivity check during setup
- Removed unreliable info endpoint check
- Improved connection logging

## [1.1.3] - 2024-11-09
### Changed
- Improved connectivity check to be more lightweight using HEAD requests
- Fixed device and entity association structure
- Unified device_info across climate and connectivity entities
- Added immediate device connectivity check during setup flow

### Fixed
- Fixed missing asyncio import in binary_sensor
- Reduced connection overhead in connectivity checks
- Fixed duplicate device creation
- Improved error handling when device is not reachable during setup
- Added early validation of device IP during configuration

## [1.1.2] - 2024-11-09
### Fixed
- Fixed device connection error related to controller.host attribute
- Fixed device_info structure to properly link climate and connectivity entities

## [1.1.1] - 2024-11-09
### Changed
- Changed domain from "intesishome" to "intesishome_local" to avoid conflicts with core integration

### Fixed
- Fixed manifest.json keys ordering
- Fixed HACS validation issues

## [1.1.0] - 2024-11-09
### Added
- Added connectivity sensor for each device
- Improved device registry handling
- Better error handling for network issues

### Changed
- Updated device model structure
- Improved state handling
- Added dynamic model detection
- Added configuration_url to device info

### Fixed
- Various bug fixes and improvements

## [1.0.0] - 2024-11-07
### Added
- Initial release
- Basic climate control functionality
- Local HTTP control support