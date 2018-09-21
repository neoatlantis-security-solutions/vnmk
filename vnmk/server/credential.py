#!/usr/bin/env python3

import os
import subprocess



class CredentialManager:

    def __init__(self, config):
        self.config = config

    def new(self, filepath):
        """Take a input filepath, encrypt it with a random key, put the key
        into firebase, and save the encrypted file to credential path."""
        if not self.config.initMode:
            raise Exception(
                "Credential initialization only works with INIT mode.")
        remoteEncryptKey = os.urandom(32).hex()


    def destroy(self):
        try:
            subprocess.run(["wipe", "-fc", self.config.credentialPath])
        except:
            pass
        try:
            os.unlink(self.config.credentialPath)
        except:
            pass
        if os.path.isfile(self.config.credentialPath):
            try:
                open(self.config.credentialPath, "w")
            except:
                pass

    def ensure(self):
        """Ensures credential file exists and is writable."""
        if not os.path.isfile(self.config.credentialPath):
            raise Exception("Credential file does not exist or deleted.")
        try:
            filename = os.urandom(16).hex() + ".test"
            testpath = os.path.dirname(self.config.credentialPath)
            fullname = os.path.join(testpath, filename)
            open(fullname, "w+")
            assert os.path.isfile(fullname)
            os.unlink(fullname)
            assert not os.path.isfile(fullname)
        except:
            raise Exception("Credential file seems not deletable.")

    def release(self):
        self.ensure()
        return open(self.config.credentialPath, "r").read()
