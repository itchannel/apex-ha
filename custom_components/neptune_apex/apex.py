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
EXTRA = "extra"
VOLUME = "volume"
VOLUME_LEFT = "volumeLeft"

# module hardware types for dosing pumps that we reference
HWTYPE_DOS = "DOS"
HWTYPE_DQD = "DQD"
HWTYPE_DOSING_PUMPS = [HWTYPE_DOS, HWTYPE_DQD]


class Apex(object):
    def __init__(self, username: str, password: str, deviceip: str):
        self.username: str = username
        self.password: str = password
        self.deviceip: str = deviceip
        self.sid: Optional[str] = None
        self.status_data: Optional[dict] = None
        self.config_data = None

    def auth(self):
        # Try logging in 3 times due to controller timeout
        tries = 0
        while (tries < 3) and (self.sid is None):
            tries += 1
            headers = {**DEFAULT_HEADERS}
            data = {"login": self.username, "password": self.password, "remember_me": False}
            url = f"http://{self.deviceip}/{REST}/login"
            logging.debug(f"fetching url for auth ({url})")
            r = requests.post(f"http://{url}", headers=headers, json=data)
            # logger.debug(r.request.body)
            # logger.debug(r.status_code)
            # logger.debug(r.text)

            if r.status_code == 200:
                self.sid = r.json()["connect.sid"]

            # XXX does there need to be some sort of sleep here?

        logger.debug(f"SID: {self.sid}")
        return self.sid is not None

    def try3(self, url_path: str, postdata: Optional[dict] = None) -> Optional[dict]:
        tries = 0
        result = None
        url = f"http://{self.deviceip}/{REST}/{url_path}"
        logging.debug(f"fetching url ({url})")
        while (tries < 3) and (result is None):
            tries += 1
            if self.auth():
                # noinspection PyTypeChecker
                headers = {**DEFAULT_HEADERS, "Cookie": "connect.sid=" + self.sid}
                if postdata is None:
                    r = requests.get(f"{url}?_={str(round(time.time()))}", headers=headers)
                else:
                    # logger.debug(postdata)
                    r = requests.put(url, headers=headers, json=postdata)

                # logger.debug(r.status_code)
                if r.status_code == 200:
                    result = r.json()
                elif r.status_code == 401:
                    self.sid = None
        # if result is not None:
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

    def set_output_state(self, device_id: str, state: str) -> Optional[dict]:
        # I gave this TYPE: OUTLET a bit of side-eye, but it seems to be fine even if the
        # target is not technically an outlet.
        logger.debug(f"set output ({device_id=}) to ({state=})")
        return self.try3(f"{STATUS}/{OUTPUTS}/{device_id}", {DID: device_id, STATUS: [state, "", "OK", ""], TYPE: OUTLET})

    def get_output(self, device_id: str, expected_ctype: Optional[str]) -> Optional[dict]:
        for output in self.config_data[OCONF]:
            if output[DID] == device_id:
                if (expected_ctype is None) or (output[CTYPE] == expected_ctype):
                    return output
                logger.error(f"output with '{DID}' = {device_id} is not the expected '{CTYPE}' (got '{output[CTYPE]}', expected '{expected_ctype}'). Double check the '{DID}' or update the output in Apex Fusion.")
                return None
        return None

    def set_program(self, device_id: str, ctype: str, code: str, force_set_ctype: bool = True) -> Optional[dict]:
        output = self.get_output(device_id, ctype if force_set_ctype else None)
        if output is not None:
            # set the ctype and program
            output[CTYPE] = ctype
            output[PROG] = code
            logger.debug(f"set output ({device_id=}) program to ({code=})")
            return self.try3(f"{CONFIG}/{OCONF}/{device_id}", output)
        else:
            logger.error(f"output '{device_id}' not found")
            return None

    def set_variable(self, device_id: str, code: str) -> Optional[dict]:
        return self.set_program(device_id, ADVANCED, code, False)

    def set_temperature(self, device_id: str, temperature: float) -> Optional[dict]:
        return self.set_program(device_id, HEATER, f"Fallback OFF\nIf Tmp < {temperature} Then ON\nIf Tmp > {temperature} Then OFF\n")

    def get_module(self, module_number: int, expected_hwtypes: Optional[list[str]] = None) -> Optional[dict]:
        for module in self.config_data[MCONF]:
            if module[ABADDR] == module_number:
                if (expected_hwtypes is None) or (module[HWTYPE] in expected_hwtypes):
                    logger.debug(f"found module #{module_number} of type: {module[HWTYPE]}")
                    return module
                logger.error(f"module #{module_number} is not the expected '{HWTYPE}' (got '{module[HWTYPE]}', expected one of [{', '.join(expected_hwtypes)}]).")
                return None
        logger.error(f"module #{module_number} not found.")
        return None

    def set_dosing_rate(self, device_id: str, profile_id: int, rate: float) -> Optional[dict]:
        # get the module and check it's a dosing pump
        module_number, pump_number = map(int, device_id.split("_"))
        module = self.get_module(module_number, HWTYPE_DOSING_PUMPS)
        if module is not None:
            # SAFETY_MARGIN
            # The Neptune DOS is NOT rated for continuous duty. To extend the life of the pump, they use
            # a 3x "safety margin" in the Fusion UI. This guarantees the pump doesn't run more than 20
            # seconds out of any given minute. The setting does NOT appear to be enforced in the
            # firmware.
            # The newer DOS Quiet Drive (DQD) IS rated for continuous use, AND uses a quieter drive
            # mechanism. Typically, we use a 2.0x margin for DOS because we can, and 1.0x for the DQD.
            safety_margin = {HWTYPE_DOS: 2.0, HWTYPE_DQD: 1.0}.get(module[HWTYPE], 3.0)

            # get the target profile from the config
            profile = self.config_data[PCONF][profile_id - 1]
            if int(profile["ID"]) != profile_id:
                logger.error(f"profile index mismatch (expected {profile_id}, got {profile['ID']}")
                return None

            # turn the pump off to start - this will enable a new profile setting to start immediately.
            # without it, the DOS will wait until the current profile period expires. we also check if
            # the requested rate is anything other than 'off'
            if (self.set_variable(device_id, "Set OFF") is not None) and (rate > 0):
                # decide how to run the rate - either mls delivered per minute, or 1ml delivered over minutes
                min_rate = 0.5
                if rate > min_rate:
                    # our input is a target rate (mL/min). we want to map this to the nearest 0.1mL/min, and
                    # then find the slowest pump speed possible to manage sound levels.
                    pump_speeds = [250, 125, 60, 25, 12, 7]
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
                        forward_direction = 1 << 4
                        mode = pump_speed_index | forward_direction

                        # the DOS profile is the mode, target amount, target time period (one minute), and
                        # dose count (we always set it to 255 until otherwise modified, so the pump will
                        # keep running - I also use an automation in HA to re-up the rate before the timer
                        # runs out - 255 minutes)
                        # XXX I wonder if the re-up can be added to this integration
                        logger.debug(f"dosing high speed speed ({rate} ml/min)")
                        profile["data"] = {"mode": mode, "amount": rate, "time": 60, "count": 255}
                    else:
                        logger.error(f"requested rate ({rate} mL / min) exceeds the supported range (limit {int(pump_speeds[0] / safety_margin)} mL / min).")
                        return None
                else:
                    # handle 0 < rate < min_rate by dosing over multiple minutes, for example,
                    # 15ml per day = 15ml / 1440 mins or 0.0104 ml/min, instead, we want 1 / rate to
                    # dose one ml every 96 minutes.
                    # "mode" is 21 (the slowest speed), "amount" is 1, "time" is the number of minutes
                    # between doses, and "count" is always 255 (until otherwise modified)
                    inv_rate = 1.0 / rate
                    logger.debug(f"dosing slow speed (1 ml / {inv_rate} mins)")
                    profile["data"] = {"mode": 21, "amount": 1, "time": int(inv_rate * 60), "count": 255}

                # we set the profile to be what we need it to be so the user doesn't have to do
                # anything except choose the profile to use (there's no way to tell if a profile is
                # in use or not, so the user has to tell us)
                profile[TYPE] = "dose"
                profile_name = profile[NAME] = f"Dose_{device_id}"

                # try to set the profile data, and if successful set the pump to it
                if self.try3(f"{CONFIG}/{PCONF}/{profile_id}", profile) is not None:
                    return self.set_variable(device_id, f"Set {profile_name}")
        else:
            logger.error(f"requested device is not a dosing pump")
        return None

    def refill_reservoir(self, device_id: str) -> Optional[dict]:
        # get the module number and pump number from the device id
        module_number, pump_number = map(int, device_id.split("_"))

        # the pump number should be either 1 or 2, but it's not a guarantee 1 didn't mean 2 if the
        # user is a programmer - blech
        if 1 <= pump_number <= 2:
            pump_index = pump_number - 1

            # find the module conf for the requested device and double check that it's a DOS or DQD pump
            module = self.get_module(module_number, HWTYPE_DOSING_PUMPS)
            if module is not None:
                module[EXTRA][VOLUME_LEFT][pump_index] = module[EXTRA][VOLUME][pump_index]
                return self.try3(f"{CONFIG}/{MCONF}/{module_number}", module)
        else:
            logger.error(f"incorrect pump number (should be 1 or 2), got {pump_number}")
        return None
