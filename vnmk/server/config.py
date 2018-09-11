#!/usr/bin/env python3

import yaml
import random
import os
import sys
import hashlib
import hmac
import time

class ConfigFile:

    def __init__(self, filename):
        read = yaml.load(open(filename, "r").read())
        self.DEBUG = read["debug"] if "debug" in read else False
        self.__credential = read["credential"]
        self.serverPort = read["server"]["port"]
        self.serverAddr = read["server"]["addr"]
        self.authCode = str(read["authcode"])
        self.userID = read["userid"]
        self.idProviders = read["id-provider"]
        self.groundStateTimeout = read["timeouts"]["ground"]
        self.excitedStateTimeout = read["timeouts"]["excited"]
        self.firebase = read["firebase"]
        self.ensureCredential()

    def ensureCredential(self):
        """Ensures credential file exists and is writable."""
        if not os.path.isfile(self.__credential):
            raise Exception("Credential file does not exist or deleted.")
        try:
            filename = os.urandom(16).hex() + ".test"
            testpath = os.path.dirname(self.__credential)
            fullname = os.path.join(testpath, filename)
            open(fullname, "w+")
            assert os.path.isfile(fullname)
            os.unlink(fullname)
            assert not os.path.isfile(fullname)
        except:
            raise Exception("Credential file seems not deletable.")

    def releaseCredential(self):
        self.ensureCredential()
        return open(self.__credential, "r").read()

    def destroyCredential(self):
        try:
            subprocess.run(["wipe", "-fc", self.__credential])
        except:
            pass
        try:
            os.unlink(self.__credential)
        except:
            pass
        if os.path.isfile(self.__credential):
            try:
                open(self.__credential, "w")
            except:
                pass

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
