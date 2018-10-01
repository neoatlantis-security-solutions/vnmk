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
        try:
            print("Try to reset user remote encrypt key...")
            db.reference("/credential/%s" % self.config.userID).set(key)
            return True
        except Exception as e:
            print(e)
            return False
        return False

    def destroyRemoteEncryptKey(self):
        self.resetCredentialRemoteEncryptKey("")
