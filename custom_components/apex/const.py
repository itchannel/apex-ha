DOMAIN = "apex"
DEVICEIP = "deviceip"
MANUFACTURER = "Neptune Apex"

# common constants
NAME = "name"
STATUS = "status"
DID = "did"
TYPE = "type"
CONFIG = "config"
INPUTS = "inputs"
OUTPUTS = "outputs"
PCONF = "pconf"
OCONF = "oconf"
ICONF = "iconf"
MCONF = "mconf"
STATE = "state"
ATTRIBUTES = "attributes"

# types
DOS = "dos"
IOTA = "iotaPump|Sicce|Syncra"
VARIABLE = "variable"
VIRTUAL = "virtual"
OUTLET = "outlet"

# control types
CTYPE = "ctype"
ADVANCED = "Advanced"
HEATER = "Heater"
PROG = "prog"

SWITCHES = {
    OUTLET: {"icon": "mdi:power-socket-au"},
    "alert": {"icon": "mdi:alert"},
    VARIABLE: {"icon": "mdi:cog"},
    "afs": {"icon": "mdi:shaker"},
    "24v": {"icon": "mdi:home-lightning-bolt-outline"},
    DOS: {"icon": "mdi:test-tube"},
    VIRTUAL: {"icon": "mdi:monitor-account"},
    IOTA: {"icon": "mdi:pump"}
}

SENSORS = {
    "Temp": {"icon": "mdi:water-thermometer", "measurement": "°C"},
    "Cond": {"icon": "mdi:shaker-outline", "measurement": "ppt"},
    "in": {"icon": "mdi:ruler", "measurement": "in"},
    "pH": {"icon": "mdi:test-tube", "measurement": " "},
    "ORP": {"icon": "mdi:test-tube", "measurement": "mV"},
    "digital": {"icon": "mdi:digital-ocean"},
    "Amps": {"icon": "mdi:lightning-bolt-circle", "measurement": "A"},
    "pwr": {"icon": "mdi:power-plug", "measurement": "W"},
    "volts": {"icon": "mdi:flash-triangle", "measurement": "V"},
    "alk": {"icon": "mdi:test-tube", "measurement": "dKh"},
    "ca": {"icon": "mdi:test-tube", "measurement": "ppm"},
    "mg": {"icon": "mdi:test-tube", "measurement": "ppm"},
    DOS: {"icon": "mdi:pump", "measurement": "mL"},
    IOTA: {"icon": "mdi:pump", "measurement": "%"},
    VARIABLE: {"icon": "mdi:cog-outline"},
    VIRTUAL: {"icon": "mdi:cog-outline"},
}

MEASUREMENTS = {
    "Celcius": "°C",
    "Faren": "°F"
}

UPDATE_INTERVAL = "update_interval"
UPDATE_INTERVAL_DEFAULT = 60
