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
    "iotaPump|Sicce|Syncra": {"icon" : "mdi:pump"},
    "Feed" :  {"icon": "mdi:shaker"},
    "gph" : {"icon": "mdi:waves-arrow-right"},
    "vortech" : {"icon": "mdi:pump"},
    "UNK" : {"icon": "mdi:help"}
    }

FEED_CYCLES = [
    {"did": "1", "name": "Feed A", "type": "Feed"},
    {"did": "2", "name": "Feed B", "type": "Feed"},
    {"did": "3", "name": "Feed C", "type": "Feed"},
    {"did": "4", "name": "Feed D", "type": "Feed"}
    ]


SENSORS = {
    "Temp": {"icon": "mdi:water-thermometer", "measurement": "°C"},
    "Cond": {"icon": "mdi:shaker-outline", "measurement": "ppt"},
    "in": {"icon": "mdi:ruler", "measurement": "in"},
    "pH": {"icon": "mdi:test-tube", "measurement": " "},
    "ORP": {"icon": "mdi:test-tube", "measurement": "mV"},
    "digital": {"icon": "mdi:digital-ocean"},
    "Amps": { "icon" : "mdi:lightning-bolt-circle", "measurement": "A"},
    "pwr": {"icon" : "mdi:power-plug", "measurement": "W"},
    "volts" : {"icon" : "mdi:flash-triangle", "measurement": "V"},
    "alk" : {"icon" : "mdi:test-tube", "measurement": "dKh"},
    "ca" : {"icon" : "mdi:test-tube", "measurement": "ppm"},
    "mg" : {"icon" : "mdi:test-tube", "measurement": "ppm"}, 
    "dos" : {"icon" : "mdi:pump", "measurement": "ml"},
    "iotaPump|Sicce|Syncra": {"icon" : "mdi:pump", "measurement": "%"},
    "variable" : {"icon" : "mdi:cog-outline"},
    "virtual" : {"icon" : "mdi:cog-outline"},
    "feed" : {"icon": "mdi:timer", "measurement": "mins"},
    "gph" : {"icon": "mdi:waves-arrow-right", "measurement": "gph"},
    "vortech" : {"icon": "mdi:pump"},
    "UNK" : {"icon": "mdi:help"}
}

MANUAL_SENSORS = [
    {"name": "Feed Cycle Countdown", "type": "feed", "did": "feed_countdown"}
]

MEASUREMENTS = {
    "Celcius" : "°C",
    "Faren": "°F"
}

UPDATE_INTERVAL = "update_interval"
UPDATE_INTERVAL_DEFAULT = 60
