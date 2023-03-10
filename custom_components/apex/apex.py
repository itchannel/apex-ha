import logging
import requests
import time
from typing import Optional
from .const import NAME, STATUS, OUTPUTS, DID, TYPE, OUTLET, CTYPE, ADVANCED, HEATER, PROG, CONFIG, PCONF, OCONF, MCONF

DEFAULT_HEADERS = {"Accept": "*/*", "Content-Type": "application/json"}

logger = logging.getLogger(__name__)

# url constants
REST = "rest"

# module constants
ABADDR = "abaddr"
HWTYPE = "hwtype"
HWTYPE_DOS = "DOS"
EXTRA = "extra"
VOLUME = "volume"
VOLUME_LEFT = "volumeLeft"


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
            r = requests.post(f"http://{self.deviceip}/{REST}/login", headers=headers, json=data)
            # logger.debug(r.request.body)
            #logger.debug(r.status_code)
            #logger.debug(r.text)

            if r.status_code == 200:
                self.sid = r.json()["connect.sid"]

            # XXX does there need to be some sort of sleep here?

        logger.debug(f"SID: {self.sid}")
        return self.sid is not None

    def try3(self, url_path: str, postdata: Optional[dict] = None) -> Optional[dict]:
        tries = 0
        result = None
        url = f"http://{self.deviceip}/{REST}/{url_path}"
        while (tries < 3) and (result is None):
            tries += 1
            if self.auth():
                # noinspection PyTypeChecker
                headers = {**DEFAULT_HEADERS, "Cookie": "connect.sid=" + self.sid}
                if postdata is None:
                    r = requests.get(f"{url}?_={str(round(time.time()))}", headers=headers)
                else:
                    #logger.debug(postdata)
                    r = requests.put(url, headers=headers, json=postdata)

                #logger.debug(r.status_code)
                if r.status_code == 200:
                    result = r.json()
                elif r.status_code == 401:
                    self.sid = None
        #if result is not None:
        #    logger.debug(result)
        return result

    def status(self) -> Optional[dict]:
        status_data = self.try3(f"status")
        if status_data is not None:
            self.status_data = status_data
        return self.status_data

    def config(self) -> Optional[dict]:
        config_data = self.try3(CONFIG)
        if config_data is not None:
            self.config_data = config_data
        return self.config_data

    def set_output_state(self, did: str, state: str) -> Optional[dict]:
        # I gave this TYPE: OUTLET a bit of side-eye, but it seems to be fine even if the
        # target is not technically an outlet.
        logger.debug(f"Set output ({did=}) to ({state=})")
        return self.try3(f"{STATUS}/{OUTPUTS}/{did}", {DID: did, STATUS: [state, "", "OK", ""], TYPE: OUTLET})

    def get_output(self, did: str, expected_ctype: Optional[str]) -> Optional[dict]:
        for output in self.config_data[OCONF]:
            if output[DID] == did:
                if (expected_ctype is None) or (output[CTYPE] == expected_ctype):
                    return output
                logger.error(f"Output with '{DID}' = {did} is not the expected '{CTYPE}' (got '{output[CTYPE]}', expected '{expected_ctype}'). Double check the '{DID}' or update the output in Apex Fusion.")
                return None
        return None

    def set_program(self, did: str, ctype: str, code: str, force_set_ctype: bool = True) -> Optional[dict]:
        output = self.get_output(did, ctype if force_set_ctype else None)
        if output is not None:
            # set the ctype and program
            output[CTYPE] = ctype
            output[PROG] = code
            logger.debug(f"Set output ({did=}) program to ({code=})")
            return self.try3(f"{CONFIG}/{OCONF}/{did}", output)
        else:
            logger.error(f"Output '{did}' not found")
            return None

    def set_variable(self, did: str, code: str) -> Optional[dict]:
        return self.set_program(did, ADVANCED, code, False)

    def set_temperature(self, did: str, temperature: float) -> Optional[dict]:
        return self.set_program(did, HEATER, f"Fallback OFF\nIf Tmp < {temperature} Then ON\nIf Tmp > {temperature} Then OFF\n")

    def set_dos_rate(self, did: str, profile_id: int, rate: float) -> Optional[dict]:
        # get the target profile from the config
        profile = self.config_data[PCONF][profile_id - 1]
        if int(profile["ID"]) != profile_id:
            logger.error(f"Profile index mismatch (expected {profile_id}, got {profile['ID']}")
            return None

        # turn the pump off to start - this will enable a new profile setting to start immediately
        # without it, the DOS will wait until the current profile period expires
        if self.set_variable(did, "Set OFF") is not None:
            # check if the requested rate is greater than the OFF threshold
            min_rate = 0.1
            if rate > min_rate:
                # our input is a target rate (mL/min). we want to map this to the nearest 0.1mL/min, and
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
                    profile[TYPE] = "dose"
                    profile_name = profile[NAME] = f"Dose_{did}"

                    # the DOS profile is the mode, target amount, target time period (one minute), and
                    # dose count
                    profile["data"] = {"mode": mode, "amount": rate, "time": 60, "count": 255}

                    # try to set the profile data, and if successful set the pump to it
                    if self.try3(f"{CONFIG}/{PCONF}/{profile_id}", profile) is not None:
                        return self.set_variable(did, f"Set {profile_name}")
                else:
                    logger.error(f"Requested rate ({rate} mL / min) exceeds the supported range (limit {int(pump_speeds[0] / safety_margin)} mL / min).")
            else:
                # XXX TODO handle 0 < rate < 0.1ml/min by dosing over multiple minutes? Is this necessary?
                logger.warning(f"dosing does not currently support < {min_rate} mL / min")
        return None

    # section of code to deal with module configuration
    def get_module(self, module_number: int, expected_hwtype: Optional[str] = None) -> Optional[dict]:
        for module in self.config_data[MCONF]:
            if module[ABADDR] == module_number:
                if (expected_hwtype is None) or (module[HWTYPE] == expected_hwtype):
                    return module
                logger.error(f"Module #{module_number} is not the expected '{HWTYPE}' (got '{module[HWTYPE]}', expected '{expected_hwtype}').")
                return None
        logger.error(f"Module #{module_number} not found.")
        return None

    def refill_dos_reservoir(self, module_number: int, pump_number: int) -> Optional[dict]:
        # the pump number should be either 1 or 2, but it's not a guarantee 1 didn't mean 2 if the
        # user is a programmer - blech
        if 1 <= pump_number <= 2:
            pump_index = pump_number - 1

            # find the module conf for the requested device and double check that it's a DOS pump
            module = self.get_module(module_number, HWTYPE_DOS)
            if module is not None:
                module[EXTRA][VOLUME_LEFT][pump_index] = module[EXTRA][VOLUME][pump_index]
                return self.try3(f"{CONFIG}/{MCONF}/{module_number}", module)
        else:
            logger.error(f"Incorrect pump number (should be 1 or 2), got {pump_number}")
        return None
