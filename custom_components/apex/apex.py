import logging
import requests
import time
from typing import Optional

DEFAULT_HEADERS = {"Accept": "*/*", "Content-Type": "application/json"}

logger = logging.getLogger(__name__)


class Apex(object):
    def __init__(self, username, password, deviceip):
        self.username = username
        self.password = password
        self.deviceip = deviceip
        self.sid = None
        self.status_data = None
        self.config_data = None

    def auth(self):
        # Try logging in 3 times due to controller timeout
        tries = 0
        while (tries < 3) and (self.sid is None):
            tries += 1
            headers = {**DEFAULT_HEADERS}
            data = {"login": self.username, "password": self.password, "remember_me": False}
            r = requests.post(f"http://{self.deviceip}/rest/login", headers=headers, json=data)
            # logger.debug(r.request.body)
            logger.debug(r.status_code)
            logger.debug(r.text)

            if r.status_code == 200:
                self.sid = r.json()["connect.sid"]

            # XXX does there need to be some sort of sleep here?
            
        logger.debug(f"SID: {self.sid}")
        return self.sid is not None

    def try3(self, url, postdata: Optional[dict] = None):
        tries = 0
        result = None
        while (tries < 3) and (result is None):
            tries += 1
            if self.auth():
                # noinspection PyTypeChecker
                headers = {**DEFAULT_HEADERS, "Cookie": "connect.sid=" + self.sid}
                if postdata is None:
                    r = requests.get(f"{url}?_={str(round(time.time()))}", headers=headers)
                else:
                    logger.debug(postdata)
                    r = requests.put(url, headers=headers, json=postdata)

                logger.debug(r.status_code)
                if r.status_code == 200:
                    result = r.json()
                elif r.status_code == 401:
                    self.sid = None
        if result is not None:
            logger.debug (result)
        return result

    def status(self):
        status_data = self.try3(f"http://{self.deviceip}/rest/status")
        if status_data is not None:
            self.status_data = status_data
        return self.status_data

    def config(self):
        config_data = self.try3(f"http://{self.deviceip}/rest/config")
        if config_data is not None:
            self.config_data = config_data
        return self.config_data

    def set_output(self, did, state):
        # I gave this "type": "outlet" a bit of side-eye, but it seems to be fine even if the
        # target is not technically an outlet.
        logger.debug(f"Set output ({did=}) to ({state=})")
        return self.try3(f"http://{self.deviceip}/rest/status/outputs/{did}", postdata={"did": did, "status": [state, "", "OK", ""], "type": "outlet"})

    def set_variable(self, did, code):
        variable = None
        for output in self.config_data["oconf"]:
            if output["did"] == did:
                variable = output

        if variable is not None:
            # set the ctype and the program
            variable["ctype"] = "Advanced"
            variable["prog"] = code
            logger.debug(f"Set variable ({did=}) program to ({code=})")
            return self.try3(f"http://{self.deviceip}/rest/config/oconf/{did}", postdata=variable)
        else:
            logger.error(f"Variable '{did}' not found")
            return None

    def set_dos_rate(self, did, profile_id, rate):
        # get the target profile from the config
        profile = self.config_data["pconf"][profile_id - 1]
        if int(profile["ID"]) != profile_id:
            logger.error(f"Profile index mismatch (expected {profile_id}, got {profile['ID']}")
            return None

        # turn the pump off to start - this will enable a new profile setting to start immediately
        # without it, the DOS will wait until the current profile period expires
        if self.set_variable(did, "Set OFF") is not None:
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

                # if the requested rate is within the supported range
                if int(pump_speeds[0] / safety_margin) >= rate:
                    # find the best speed match
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
                    profile_name = profile["name"] = f"Dose_{did}"

                    # the DOS profile is the mode, target amount, target time period (one minute), and
                    # dose count
                    profile["data"] = {"mode": mode, "amount": rate, "time": 60, "count": 255}

                    # try to set the profile data, and if successful set the pump to it
                    if self.try3(f"http://{self.deviceip}/rest/config/pconf/{profile_id}", postdata=profile) is not None:
                        return self.set_variable(did, f"Set {profile_name}")
                else:
                    logger.error(f"Requested rate ({rate} mL / min) exceeds the supported range (limit {int(pump_speeds[0] / safety_margin)} mL / min).")
            else:
                # XXX TODO handle 0 < rate < 0.1ml/min by dosing over multiple minutes? Is this necessary?
                logger.warning(f"dosing does not currently support < {min_rate} mL / min")
        return None
