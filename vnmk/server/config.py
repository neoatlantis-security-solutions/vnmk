#!/usr/bin/env python3

import yaml
import random
import os
import sys
import hashlib
import hmac
import time

from .firebase import Firebase
from .credential import CredentialManager


class ConfigFile:

    def __init__(self, filename, initMode=False):
        read = yaml.load(open(filename, "r").read())
        self.DEBUG = read["debug"] if "debug" in read else False
        self.credentialPath = read["credential"]
        self.initMode = initMode
        self.serverPort = read["server"]["port"]
        self.serverAddr = read["server"]["addr"]
        self.authCode = str(read["authcode"])
        self.userID = read["userid"]
        self.idProviders = read["id-provider"]
        self.groundStateTimeout = read["timeouts"]["ground"]
        self.excitedStateTimeout = read["timeouts"]["excited"]
        self.firebaseConfig = read["firebase"]

        self.firebase = Firebase(self)
        self.credential = CredentialManager(self)


    def __str__(self):
        return yaml.dump({
            "server": {
                "addr": self.serverAddr,
                "port": self.serverPort,
            },
            "credential": self.credential,
            "authcode": self.authCode,
            "userid": self.userID,
        }, default_flow_style=False)
