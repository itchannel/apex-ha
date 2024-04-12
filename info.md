## **Changelog**

## Version 1.14.5
 - Debug Login and Added Basic Auth FallBack

## Version 1.14
- Fix update error
- Strip "L" from version information for certain devices
## Version 1.13
- Add Feed Cycle Switches
## Version 1.12
- Fix "any" bug on device update
## Version 1.11
- Added ability to update firmware of Apex device via HA
- Fixed IOT and polling class types

## Version 1.10
- Dos control service (@brettonw)
- Error handling fixes (@brettonw)
- Added open source license
- Fix "TEST" error on HA 2023.8
- Add translation strings for services HA 2023.8
- Enable HA debugging button for integration

## Version 1.09

- Add set_variable service for setting programming code in variables e.g. "Set 75" 
- Fix cookie expiry bug

## Version 1.08

- Bug fix for config error on old status.xml file

### Version 1.07

- Change naming scheme for entities to start with apex\_ **Breaking change: This will create duplicate entities as the naming scheme has changed and any existing automations will need to be updated to the new format**
- Add retrieval of measurements from Apex config e.g. temp probes report correct Celcius or Fahrenheit
- Add support for older Apex systems using status.xml (Currently read only, switches will not toggle as it's unauthenticated only)
- Add support for device (iotaPump|Sicce|Syncra)

### Version 1.06

- Change update interval to seconds instead of minutes as requested (Be aware quicker than 30 second polling can crash the controller)
- Add DOS bottle levels to sensor data
- Add more icons and measurements for missing sensors

### Version 1.05

- Add update interval to options
- Add set_output service to allow setting to OFF/ON/AUTO (Switches only support OFF/ON in HA)

### Version 1.04

- Update translations file for hacfest workflow

### Version 1.03

- Fixed "AON" status for outputs

### Version 1.02

- Remove excess logging code

### Version 1.01

- Fix coordinator updates

### Version 1.00

- Initial release of integration
