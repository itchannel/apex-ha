# Local Apex Controller integration for Home Assistant (https://www.neptunesystems.com/)

This is a home assistant integration for the Neptune Apex line of aquarium controllers. Currently support has only been tested on the Neptune Apex Jr, however it should work for all. Inputs and Outputs are currently supported in the form of sensors and switches.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/itchannel)

## Install

Use HACS and add as a custom repo. Once the integration is installed go to your integrations and follow the configuration options to specify the below:

- Username (Apex Controller Username)
- Password (Apex Controller Password)
- Apex Controller IP Address

## Older versions (Apex Jnr, Apex Classic)

Older versions of the Apex controller don't support the rest API , however basic support has been added by @dkramarc which allows controlling switches and reading values using basic auth and the legacy API.

## Options

You can set the update interval that the integration polls the controller (in seconds). Be aware you will need to reload the integration once updating options for this to take affect.

This is a diy integration and is not supported or affiliated with Neptune Systems.
