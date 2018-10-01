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
from .gpgdecrypt import GPGDecrypt


class ConfigFile:

    def __init__(self, filename, initMode=False):
        if filename.endswith(".gpg"):
            configYAML = GPGDecrypt(filename)
        else:
            configYAML = open(filename, "r").read()
        read = yaml.load(configYAML)
        self.DEBUG = read["debug"] if "debug" in read else False

        basedir = os.path.realpath(os.path.dirname(filename))
        workdir = os.path.join(basedir, read["workdir"])
        self.workdir = lambda *d: os.path.join(workdir, *d)

        self.credentialPath = self.workdir("credential.txt")
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
