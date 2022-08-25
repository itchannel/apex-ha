DOMAIN = "apex"
DEVICEIP = "deviceip"
MANUFACTURER = "Neptune Apex"

SWITCHES = {
    "outlet": {"icon": "mdi:power-socket-au"}, 
    "alert": {"icon": "mdi:alert"}, 
    "variable": {"icon": "mdi:cog"},
    "afs": {"icon": "mdi:shaker"},
    "24v": {"icon": "mdi:home-lightning-bolt-outline"},
    "dos": {"icon": "mdi:test-tube"},
    "virtual": {"icon": "mdi:monitor-account"},
    "iotaPump|Sicce|Syncra", {"icon" : "mdi:pump"}
    }

SENSORS = {
    "Temp": {"icon": "mdi:water-thermometer", "measurement": "°C"},
    "Cond": {"icon": "mdi:shaker-outline"}, 
    "pH": {"icon": "mdi:test-tube", "measurement": "pH"},
    "ORP": {"icon": "mdi:test-tube"},
    "digital": {"icon": "mdi:digital-ocean"},
    "Amps": { "icon" : "mdi:lightning-bolt-circle", "measurement": "A"},
    "pwr": {"icon" : "mdi:power-plug", "measurement": "W"},
    "volts" : {"icon" : "mdi:flash-triangle", "measurement": "V"},
    "alk" : {"icon" : "mdi:test-tube", "measurement": "dKh"},
    "ca" : {"icon" : "mdi:test-tube", "measurement": "ppm"},
    "mg" : {"icon" : "mdi:test-tube", "measurement": "ppm"}, 
    "dos" : {"icon" : "mdi:pump", "measurement": "ml"},
    "iotaPump|Sicce|Syncra", {"icon" : "mdi:pump", "measurement": "%"}
}

MEASUREMENTS = {
    "Celcius" : "°C",
    "Faren": "°F"
}

UPDATE_INTERVAL = "update_interval"
UPDATE_INTERVAL_DEFAULT = 60