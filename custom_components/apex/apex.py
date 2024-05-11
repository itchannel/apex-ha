import logging
import requests
import time
import xmltodict
import base64
import json

defaultHeaders = {
    "Accept": "*/*",
    "Content-Type": "application/json"
}

_LOGGER = logging.getLogger(__name__)


class Apex(object):
    def __init__(
            self, username, password, deviceip
    ):

        self.username = username
        self.password = password
        self.deviceip = deviceip
        self.sid = None
        self.version = "new"
        self.did_map = {}

    def auth(self):
        headers = {**defaultHeaders}
        data = {"login": self.username, "password": self.password, "remember_me": False}
        login_attempt = 0

        while login_attempt < 3:
            r = requests.post(f"http://{self.deviceip}/rest/login", headers=headers, json=data)

            _LOGGER.debug(f"Attempt {login_attempt + 1}: Sending POST request to http://{self.deviceip}/rest/login")
            _LOGGER.debug(f"Response status code: {r.status_code}")
            # _LOGGER.debug(f"Response body: {r.text}")

            if r.status_code == 200:
                self.sid = r.json().get("connect.sid", None)
                if self.sid:
                    _LOGGER.debug(f"Successfully authenticated with session. Session ID: {self.sid}")
                    return True
                else:
                    _LOGGER.error("Session ID missing in the response.")
            elif r.status_code == 404:
                self.version = "old"
                _LOGGER.info("Detected old version of the device software.")
                return True
            elif r.status_code != 401:
                _LOGGER.warning(f"Unexpected status code: {r.status_code}")
            else:
                _LOGGER.info(f"Basic Auth attempt because of 401 error")
                # Basic Auth fallback
                basic_auth_header = base64.b64encode(f"{self.username}:{self.password}".encode()).decode('utf-8')
                headers['Authorization'] = f"Basic {basic_auth_header}"
                r = requests.post(f"http://{self.deviceip}/", headers=headers)

                _LOGGER.debug(f"Basic Auth Response status code: {r.status_code}")
                # _LOGGER.debug(f"Basic Auth Response body: {r.text}")

                if r.status_code == 200:
                    self.version = "old"
                    self.sid = f"Basic {basic_auth_header}"
                    _LOGGER.info("Successfully authenticated using Basic Auth.")
                    _LOGGER.debug(f"Basic Auth SID: {self.sid}")
                    return True
                else:
                    _LOGGER.error("Failed to authenticate using both methods.")

            login_attempt += 1
            if login_attempt < 3:
                _LOGGER.info(f"Retrying authentication... Attempt #{login_attempt + 1}")

        _LOGGER.error("Authentication failed after 3 attempts.")
        return False


    def oldstatus(self):
        headers = {**defaultHeaders}
        headers['Authorization'] = self.sid

        r = requests.get(f"http://{self.deviceip}/cgi-bin/status.xml?" + str(round(time.time())), headers=headers)
        _LOGGER.debug(f"oldstatus: Response status code: {r.status_code}")
        # _LOGGER.debug(f"oldstatus: Response body: {r.text}")

        xml = xmltodict.parse(r.text)
        # _LOGGER.debug("oldstatus: XML parsed successfully")

        result = {}
        system = {}
        system["software"] = xml["status"]["@software"]
        system["hardware"] = xml["status"]["@hardware"] + " Legacy Version (Status.xml)"
        result["system"] = system
        # _LOGGER.debug(f"oldstatus: system: {system}")

        inputs = []
        # Ensure the 'probe' key exists and is a list
        probes = xml["status"]["probes"].get("probe", [])
        if not isinstance(probes, list):
            probes = [probes]  # Make it a single-item list if it's not a list

        for value in probes:
            inputdata = {}
            inputdata["did"] = "base_" + value["name"]
            inputdata["name"] = value["name"]
            # Using get to provide a default value of 'variable' if 'type' is not found
            inputdata["type"] = value.get("type", "variable")
            inputdata["value"] = value["value"].strip()  # Also stripping any whitespace from the value
            inputs.append(inputdata)

        result["inputs"] = inputs
        # _LOGGER.debug(f"oldstatus: inputs: {inputs}")

        outputs = []
        for value in xml["status"]["outlets"]["outlet"]:
            outputdata = {}
            outputdata["did"] = value["deviceID"]
            outputdata["name"] = value["name"]
            outputdata["status"] = [value["state"], "", "OK", ""]
            outputdata["id"] = value["outputID"]
            outputdata["type"] = "outlet"
            outputs.append(outputdata)
            self.did_map[value["deviceID"]] = value["name"]

        result["outputs"] = outputs
        # _LOGGER.debug(f"oldstatus: outputs: {outputs}")

        _LOGGER.debug(f"oldstatus result: {result}")
        return result

    def oldstatus_json(self):
        i = 0
        while i <= 3:
            headers = {**defaultHeaders}
            headers['Authorization'] = self.sid

            r = requests.get(f"http://{self.deviceip}/cgi-bin/status.json?" + str(round(time.time())), headers=headers)
            # _LOGGER.debug(f"oldstatus_json: Response status code: {r.status_code}")
            # _LOGGER.debug(f"oldstatus_json: Response body: {r.text}")

            if r.status_code == 200:
                json_in = r.json()
                # _LOGGER.debug(f"oldstatus_json: json_in: {json_in}")

                # data comes in istat so move it to root of results
                result = json_in["istat"];

                # generate system info
                system = {}
                system["software"] = result["software"]
                system["hardware"] = result["hostname"] + " " + result["hardware"] + " " + result["serial"]
                result["system"] = system
                # _LOGGER.debug(f"oldstatus_json: system: {system}")

                # Add Apex type for Feed Calculation
                result["feed"]["apex_type"] = "old"

                # Parse outputs to get name for map (for toggle)
                outputs = result["outputs"]
                for output in outputs:
                    did = output["did"]
                    name = output["name"]
                    self.did_map[did] = name
                # _LOGGER.debug(f"oldstatus_json: did_map: {self.did_map}")

                #_LOGGER.debug(f"oldstatus_json result: {result}")
                return result
            elif r.status_code == 401:
                self.auth()
            else:
                _LOGGER.debug("oldstatus_json: Unknown error occurred")
                return {}
            i += 1



    def status(self):

        _LOGGER.debug(f"status grab for {self.version}: sid[{self.sid}]")

        if self.sid is None:
            _LOGGER.debug("We are none")
            self.auth()

        if self.version == "old":
            # result = self.oldstatus()
            result = self.oldstatus_json()
            return result

        i = 0
        while i <= 3:
            headers = {**defaultHeaders, "Cookie": "connect.sid=" + self.sid}
            r = requests.get(f"http://{self.deviceip}/rest/status?_=" + str(round(time.time())), headers=headers)
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

        r = requests.get(f"http://{self.deviceip}/rest/config?_=" + str(round(time.time())), headers=headers)
        # _LOGGER.debug(r.text)

        if r.status_code == 200:
            return r.json()
        else:
            print("Error occurred")

    def toggle_output(self, did, state):
        # _LOGGER.debug(f"toggle_output [{self.version}]: did[{did}] state[{state}]")

        if self.version == "old":
            headers = {**defaultHeaders}
            headers['Authorization'] = self.sid
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

            # 1 = OFF, 0 = AUTO, 2 = ON
            state_value = 1
            ret_state = "OFF"
            if state == "ON":
                state_value = 2
                ret_state = "ON"
            if state == "AOF":
                state_value = 0
                ret_state = "OFF"
            if state == "AON":
                state_value = 0
                ret_state = "ON"

            object_name = self.did_map[did]

            data = f"{object_name}_state={state_value}&noResponse=1"
            _LOGGER.debug(f"toggle_output [old] Out Data: {data}")

            headers['Content-Length'] = f"{len(data)}"
            _LOGGER.debug(f"toggle_output [old] Headers: {headers}")

            try:
                url = f"http://{self.deviceip}/cgi-bin/status.cgi"
                r = requests.post(url, headers=headers, data=data, proxies={"http": None, "https": None})
                _LOGGER.debug(f"toggle_output [old] ({r.status_code}): {r.text}")
            except Exception as e:
                _LOGGER.debug(f"toggle_output [old] Exception: {e}")

            status_data = {
                "status": [ret_state],
            }
            return status_data


        headers = {**defaultHeaders, "Cookie": "connect.sid=" + self.sid}

        # I gave this "type": "outlet" a bit of side-eye, but it seems to be fine even if the
        # target is not technically an outlet.
        data = {"did": did, "status": [state, "", "OK", ""], "type": "outlet"}
        _LOGGER.debug(data)

        r = requests.put(f"http://{self.deviceip}/rest/status/outputs/" + did, headers=headers, json=data)
        data = r.json()
        _LOGGER.debug(data)
        return data

    def toggle_feed_cycle(self, did, state):
        _LOGGER.debug(f"toggle_feed_cycle [{self.version}]: did[{did}] state[{state}]")

        if self.version == "old":

            # Feed A-D: (0/3)
            # FeedCycle=Feed&FeedSel=3&noResponse=1
            # Cancel (5)
            # FeedCycle=Feed&FeedSel=5&noResponse=1

            feed_selection_map = {
                "1": "0",
                "2": "1",
                "3": "2",
                "4": "3"
            }

            # Default to Cancel/OFF
            FeedSel = "5"
            # ret_state: 1 = ON, 92 = OFF
            ret_state = 92
            ret_did = 6   # 6 is Off

            # If Start Feed then map to FeedSel needed
            if state == "ON" and did in feed_selection_map:
                FeedSel = feed_selection_map[did]
                ret_state = 1
                ret_did = did

            headers = {**defaultHeaders}
            headers['Authorization'] = self.sid
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

            data = f"FeedCycle=Feed&FeedSel={FeedSel}&noResponse=1"
            # _LOGGER.debug(f"toggle_feed_cycle [old] Out Data: {data}")

            headers['Content-Length'] = f"{len(data)}"
            # _LOGGER.debug(f"toggle_feed_cycle [old] Headers: {headers}")

            try:
                url = f"http://{self.deviceip}/cgi-bin/status.cgi"
                r = requests.post(url, headers=headers, data=data, proxies={"http": None, "https": None})
                _LOGGER.debug(f"toggle_feed_cycle [old] ({r.status_code}): {r.text}")
            except Exception as e:
                _LOGGER.debug(f"toggle_feed_cycle [old] Exception: {e}")

            status_data = {
                "active": ret_state,
                "errorCode": 0,
                "errorMessage": "",
                "name": ret_did,
                "apex_type:": "old"
            }
            return status_data


        headers = {**defaultHeaders, "Cookie": "connect.sid=" + self.sid}
        if state == "ON":
            data = {"active": 1, "errorCode": 0, "errorMessage": "", "name": did}

            r = requests.put(f"http://{self.deviceip}/rest/status/feed/" + did, headers=headers, json=data)
        elif state == "OFF":
            data = {"active": 92, "errorCode": 0, "errorMessage": "", "name": 0}
            _LOGGER.debug(data)

            r = requests.put(f"http://{self.deviceip}/rest/status/feed/0" , headers=headers, json=data)
        _LOGGER.debug(data)

        data = r.json()
        _LOGGER.debug(data)
        return data

    def set_variable(self, did, code):
        if self.version == "old":
            return {"error": "Not available on Apex Classic"}

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

        r = requests.put(f"http://{self.deviceip}/rest/config/oconf/" + did, headers=headers, json=variable)
        _LOGGER.debug(r.text)

        return {"error": ""}
    
    def update_firmware(self):
        if self.version == "old":
            return {"error": "Not available on Apex Classic"}

        headers = {**defaultHeaders, "Cookie": "connect.sid=" + self.sid}
        config = self.config()

        nconf = config["nconf"]

        nconf["updateFirmware"] = True

        r = requests.put(f"http://{self.deviceip}/rest/config/nconf", headers=headers, json=nconf)
        _LOGGER.debug(r.text)
        _LOGGER.debug(r.status_code)
        if (r.status_code == 200):
            return True
        else:
            return False

    def set_dos_rate(self, did, profile_id, rate):

        if self.version == "old":
            return {"error": "Not available on Apex Classic"}

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
