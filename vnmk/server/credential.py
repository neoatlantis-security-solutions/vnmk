#!/usr/bin/env python3

import os
import subprocess
import base64

from nacl.secret import SecretBox


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

    def encryptCredential(self, key, data):
        """Credential will be only encrypted here. Decryption is done via
        Javascript later at client browser."""
        assert type(key) == bytes and len(key) == 32
        assert type(data) == bytes
        box = SecretBox(key)
        return base64.b64encode(box.encrypt(data)).decode("ascii")

    def ensure(self, exists=True, deletable=True):
        """Ensures credential file exists and is deletable."""
        if exists and not os.path.isfile(self.config.credentialPath):
            raise Exception("Credential file does not exist or deleted.")
        if deletable:
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
