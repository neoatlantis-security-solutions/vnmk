#!/usr/bin/env python3

import os
import base64


def initialize(config, statemanager, credentialPath):
    # Initialize the system. 
    # Set new ground state initials at Firebase.
    # Encrypt the new credential with a custom secret.
    # Store the encrypted credential locally.
    # Upload the secret to firebase.
    # Terminate and call for another run.
    assert config.initMode
    firebase = config.firebase
    credential = config.credential

    remoteEncryptKey = os.urandom(32)
    encryptedCredential = credential.encryptCredential(
        remoteEncryptKey,
        open(credentialPath, "rb").read()
    )

    try:
        credential.ensure(exists=False, deletable=True)
        open(config.credentialPath, "w+").write(encryptedCredential)
        credential.ensure(exists=True, deletable=True)
        assert open(config.credentialPath, "r").read() == encryptedCredential
        print("Successfully saved credential.")
    except Exception as e:
        raise Exception("Failed creating credential file: %s" % e)

    encodedREK = base64.b64encode(remoteEncryptKey).decode("ascii")

    if config.firebase.resetCredentialRemoteEncryptKey(encodedREK):
        print("System state reset successful.")
        print("Credential encrypted as follows.")
        print("----")
        print(encryptedCredential)
        print("----")
        print("You may deploy this credential manually to the server.")
    else:
        print("System state reset failed. Please do that again.")
