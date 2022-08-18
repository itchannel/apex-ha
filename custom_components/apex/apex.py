import json
import logging
import requests
import time


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



    def auth(self):
        print("Logging In")
        headers = {
            **defaultHeaders
        }
        data = {
            "login" : self.username, 
            "password": self.password, 
            "remember_me" : False
        }


        r = requests.post(
            "http://" + self.deviceip + "/rest/login",
            headers = headers,
            json = data
        )

        print(r.text)
        print(r.request.body)
        print(r.status_code)
       # _LOGGER.debug(r.text)
       # _LOGGER.debug(r.request.body)

        if r.status_code == 200:
            result = r.json()
            self.sid = result["connect.sid"]
            return True
        else:
            print("Status code failure")
            return False

    def status(self):
        _LOGGER.debug(self.sid)
        if self.sid is None:
            _LOGGER.debug("We are none")
            self.auth()
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



