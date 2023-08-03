## **Changelog**
## Version 1.10
- Dos control service (@brettonw)
- Error handling fixes (@brettonw)
- Added open source license
- Fix "TEST" error on HA 2023.8
- Add translation strings for services HA 2023.8

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
