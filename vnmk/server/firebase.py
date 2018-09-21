#!/usr/bin/env python3

import firebase_admin
from firebase_admin import credentials, auth, db

class Firebase:

    def __init__(self, config):
        self.config = config
        firebaseConfig = config.firebaseConfig
        cred = credentials.Certificate(firebaseConfig["credential"])
        self.app = firebase_admin.initialize_app(cred, {
            "databaseURL": firebaseConfig["URL"],
            'databaseAuthVariableOverride': {
                'uid': '__python-server__' + \
                    ("/init" if config.initMode else ""),
            }
        })

    def issueCustomToken(self):
        return auth.create_custom_token(
            self.config.userID,
            {
                "initializing": self.config.initMode,
                "customized": True,
            }
        ).decode("ascii")

    def resetCredentialRemoteEncryptKey(self, key):
        assert type(key) == str
        if not self.config.initMode:
            raise Exception(
                "Resetting remote encrypt key only works within INIT mode.")
        try:
            db.reference("/credential/%s" % self.config.userID).set(key)
            return True
        except:
            return False
