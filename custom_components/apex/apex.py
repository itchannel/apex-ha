import logging
import requests
import time
import xmltodict

defaultHeaders = {
    "Accept": "*/*",
    "Content-Type": "application/json"
}

_LOGGER = logging.getLogger(__name__)


class Apex(object):
    def __init__(self, username, password, deviceip):
        self.username = username
        self.password = password
        self.deviceip = deviceip
        self.sid = None
        self.version = "new"

    def auth(self):
        headers = {**defaultHeaders}
        data = {"login": self.username, "password": self.password, "remember_me": False}
        # Try logging in 3 times due to controller timeout
        login = 0
        while login < 3:
            r = requests.post("http://" + self.deviceip + "/rest/login", headers=headers, json=data)
            # _LOGGER.debug(r.request.body)
            _LOGGER.debug(r.status_code)
            _LOGGER.debug(r.text)

            if r.status_code == 200:
                self.sid = r.json()["connect.sid"]
                return True
            if r.status_code == 404:
                self.version = "old"
                return True
            else:
                print("Status code failure")
                login += 1

            # XXX does there need to be some sort of sleep here?

        return False

    def oldstatus(self):
        # Function for returning information on old controllers (Currently not authenticated)
        headers = {**defaultHeaders}

        r = requests.get("http://" + self.deviceip + "/cgi-bin/status.xml?" + str(round(time.time())), headers=headers)
        xml = xmltodict.parse(r.text)
        # Code to convert old style to new style json
        result = {}
        system = {}
        system["software"] = xml["status"]["@software"]
        system["hardware"] = xml["status"]["@hardware"] + " Legacy Version (Status.xml)"

        result["system"] = system

        inputs = []
        for value in xml["status"]["probes"]["probe"]:
            inputdata = {}
            inputdata["did"] = "base_" + value["name"]
            inputdata["name"] = value["name"]
            inputdata["type"] = value["type"]
            inputdata["value"] = value["value"]
            inputs.append(inputdata)

        result["inputs"] = inputs

        outputs = []
        for value in xml["status"]["outlets"]["outlet"]:
            _LOGGER.debug(value)
            outputdata = {}
            outputdata["did"] = value["deviceID"]
            outputdata["name"] = value["name"]
            outputdata["status"] = [value["state"], "", "OK", ""]
            outputdata["id"] = value["outputID"]
            outputdata["type"] = "outlet"
            outputs.append(outputdata)

        result["outputs"] = outputs

        _LOGGER.debug(result)
        return result

    def status(self):
        _LOGGER.debug(self.sid)
        if self.sid is None:
            _LOGGER.debug("We are none")
            self.auth()

        if self.version == "old":
            result = self.oldstatus()
            return result
        i = 0
        while i <= 3:
            headers = {**defaultHeaders, "Cookie": "connect.sid=" + self.sid}
            r = requests.get("http://" + self.deviceip + "/rest/status?_=" + str(round(time.time())), headers=headers)
            # _LOGGER.debug(r.text)

            if r.status_code == 200:
                return r.json()
            elif r.status_code == 401:
                self.auth()
            else:
                _LOGGER.debug("Unknown error occurred")
                return {}
            i += 1

    def config(self):
        if self.version == "old":
            result = {}
            return result
        if self.sid is None:
            _LOGGER.debug("We are none")
            self.auth()
        headers = {**defaultHeaders, "Cookie": "connect.sid=" + self.sid}

        r = requests.get("http://" + self.deviceip + "/rest/config?_=" + str(round(time.time())), headers=headers)
        # _LOGGER.debug(r.text)

        if r.status_code == 200:
            return r.json()
        else:
            print("Error occured")

    def set_output(self, did, state):
        headers = {**defaultHeaders, "Cookie": "connect.sid=" + self.sid}

        # I gave this "type": "outlet" a bit of side-eye, but it seems to be fine even if the
        # target is not technically an outlet.
        data = {"did": did, "status": [state, "", "OK", ""], "type": "outlet"}
        _LOGGER.debug(data)

        r = requests.put("http://" + self.deviceip + "/rest/status/outputs/" + did, headers=headers, json=data)
        data = r.json()
        _LOGGER.debug(data)
        return data

    def set_variable(self, did, code):
        headers = {**defaultHeaders, "Cookie": "connect.sid=" + self.sid}
        config = self.config()
        variable = None
        for value in config["oconf"]:
            if value["did"] == did:
                variable = value

        if variable is None:
            return {"error": "Variable/did not found"}

        # I don't think it's necessary to warn on this, that just forces me to go to the Apex
        # interface and set it...
        # if variable["ctype"] != "Advanced":
        #     _LOGGER.debug("Only Advanced mode currently supported")
        #     return {"error": "Given variable was not of type Advanced"}

        variable["ctype"] = "Advanced"
        variable["prog"] = code
        _LOGGER.debug(variable)

        r = requests.put("http://" + self.deviceip + "/rest/config/oconf/" + did, headers=headers, json=variable)
        _LOGGER.debug(r.text)

        return {"error": ""}

    def set_dos_rate(self, did, profile_id, rate):
        headers = {**defaultHeaders, "Cookie": "connect.sid=" + self.sid}
        config = self.config()

        profile = config["pconf"][profile_id - 1]
        if int(profile["ID"]) != profile_id:
            return {"error": "Profile index mismatch"}

        # turn the pump off to start - this will enable a new profile setting to start immediately
        # without it, the DOS will wait until the current profile period expires
        off = self.set_variable(did, f"Set OFF")
        if off["error"] != "":
            return off

        # check if the requested rate is greater than the OFF threshold
        min_rate = 0.1
        if rate > min_rate:
            # our input is a target rate (ml/min). we want to map this to the nearest 0.1ml/min, and
            # then find the slowest pump speed possible to manage sound levels. Neptune uses a 3x
            # safety margin to extend the life of the pump, but the setting only appears to be
            # enforced in the Fusion UI. We use a 2x margin because we can.
            pump_speeds = [250, 125, 60, 25, 12, 7]
            safety_margin = 2
            rate = int(rate * 10) / 10.0
            if int(pump_speeds[0] / safety_margin) >= rate:
                target_pump_speed = rate * safety_margin
                pump_speed_index = len(pump_speeds) - 1
                while pump_speeds[pump_speed_index] < target_pump_speed:
                    pump_speed_index -= 1

                # bits 0-4 of the 'mode' value are the pump speed index, and bit 5 specifies
                # 'forward' or 'reverse'. we always use 'forward' because you can't calibrate the
                # reverse direction using the Apex dashboard
                mode = pump_speed_index + 16

                # we set the profile to be what we need it to be so the user doesn't have to do
                # anything except choose the profile to use
                profile["type"] = "dose"
                profile["name"] = f"Dose_{did}"

                # the DOS profile is the mode, target amount, target time period (one minute), and
                # dose count
                profile["data"] = {"mode": mode, "amount": rate, "time": 60, "count": 255}
                _LOGGER.debug(profile)

                r = requests.put(f"http://{self.deviceip}/rest/config/pconf/{profile_id}", headers=headers, json=profile)
                # _LOGGER.debug(r.text)

                # turn the pump on
                return self.set_variable(did, f"Set {profile['name']}")
            else:
                return {"error": f"Requested rate ({rate} mL / min) exceeds the supported range (limit {int(pump_speeds[0] / safety_margin)} mL / min)."}
        else:
            # XXX TODO handle 0 < rate < 0.1ml/min by dosing over multiple minutes? Is this necessary?
            return {"error": ""}
