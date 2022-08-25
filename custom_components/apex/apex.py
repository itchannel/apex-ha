import json
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
    def __init__(
        self, username, password, deviceip
    ):

        self.username = username
        self.password = password
        self.deviceip = deviceip
        self.sid = None
        self.version = "new"



    def auth(self):
        headers = {
            **defaultHeaders
        }
        data = {
            "login" : self.username, 
            "password": self.password, 
            "remember_me" : False
        }
        # Try logging in 3 times due to controller timeout
        login = 0
        while login < 3:
            r = requests.post(
                "http://" + self.deviceip + "/rest/login",
                headers = headers,
                json = data
            )


            _LOGGER.debug(r.text)
            _LOGGER.debug(r.status_code)
        # _LOGGER.debug(r.text)
        # _LOGGER.debug(r.request.body)

            if r.status_code == 200:
                result = r.json()
                self.sid = result["connect.sid"]
                return True
            if r.status_code == 404:
                self.version = "old"
                return True
            else:
                print("Status code failure")
                login += 1
        return False

    def oldstatus(self):
        # Function for returning information on old controllers (Currently not authenticated)
        headers = {
            **defaultHeaders
        }

        r = requests.get(
            "http://" + self.deviceip + "/cgi-bin/status.xml?" + str(round(time.time())),
            headers = headers
        )
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
        headers = {
            **defaultHeaders,
            "Cookie" : "connect.sid=" + self.sid
        }

        r = requests.get(
            "http://" + self.deviceip + "/rest/status?_=" + str(round(time.time())),
            headers = headers
        )
        #_LOGGER.debug(r.text)

        if r.status_code == 200:
            result = r.json()
            return result
        else:
            print("Error occured")

    def config(self):

        if self.version == "old":
            result = {}
            return result
        if self.sid is None:
            _LOGGER.debug("We are none")
            self.auth()
        headers = {
            **defaultHeaders,
            "Cookie" : "connect.sid=" + self.sid
        }

        r = requests.get(
            "http://" + self.deviceip + "/rest/config?_=" + str(round(time.time())),
            headers = headers
        )
        #_LOGGER.debug(r.text)

        if r.status_code == 200:
            result = r.json()
            return result
        else:
            print("Error occured")

    def toggle_output(self, did, state):
        headers = {
            **defaultHeaders,
            "Cookie" : "connect.sid=" + self.sid
        }

        data = {
            "did" : did, 
            "status": [
                state, 
                "", 
                "OK", 
                ""
            ],
            "type": "outlet"

        }

        _LOGGER.debug(data)

        r = requests.put(
            "http://" + self.deviceip + "/rest/status/outputs/" + did, 
            headers = headers,
            json = data
        )
        data = r.json()
        _LOGGER.debug(data)
        return data



