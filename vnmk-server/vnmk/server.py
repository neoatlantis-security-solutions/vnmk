#!/usr/bin/env python3

import bottle
import random
import os
import sys
import time
import json

from .config import ConfigFile
from .authenticator import Authenticator

BASEPATH = os.path.dirname(sys.argv[0])
fullpath = lambda *i: os.path.join(BASEPATH, *i)


def renderTemplate(filename, **arguments):
    fullname = fullpath("static", filename)
    return bottle.template(open(fullname, "r").read(), **arguments)

def jsonAnswer(error=None, result=None):
    return json.dumps({
        "error": error,
        "result": result, 
    })

def runServer(config):
    assert isinstance(config, ConfigFile)
    authenticator = Authenticator(config)

    SESSION_START_TIME = -1

    class RandomIntentVerifier:
        """Generates a code based on time. This is a simple prevention of
        accidential open of a session, by asking the user to input a 4-digit
        code that is displayed, which is valid for 30 seconds."""
        def __getCode(self):
            return str(int(time.time() / 30))[-4:]
        def __call__(self, u, p):
            if SESSION_START_TIME > 0:
                # Fast-track to login page, when count down already started.
                return True
            return p.lower().strip() == self.__getCode()\
                or u.lower().strip() == self.__getCode() 
        def __str__(self):
            return "Input '%s' as username or password, " % self.__getCode() +\
                "to confirm you really want to visit this page."

    def updateCredential():
        nonlocal SESSION_START_TIME
        config.ensureCredential() # Ensure credential accessible & destroyable
        if\
            SESSION_START_TIME > 0 and \
            SESSION_START_TIME + config.sessionTimeout < time.time()\
            :
            config.destroyCredential()
            SESSION_START_TIME = -1
            raise Exception("Credential destroyed due to session timeout.")

    # ---- Serves static files

    @bottle.get("/static/<filename>")
    def serveStatic(filename):
        return bottle.static_file(filename, root=fullpath("static"))

    # ---- Handles interface page for user login, which also includes starting
    #      the count down.

    randomIntentVerifier = RandomIntentVerifier()
    @bottle.get("/<uid>/")
    @bottle.auth_basic(
        randomIntentVerifier,
        realm=randomIntentVerifier,
        text=randomIntentVerifier
    )
    def createSession(uid):
        nonlocal SESSION_START_TIME
        if uid != config.userID:
            return renderTemplate(
                "error.html", 
                description="Invalid access URL."
            )
        if SESSION_START_TIME < 0:
            SESSION_START_TIME = time.time()
        try:
            updateCredential()
        except Exception as reason:
            return renderTemplate("error.html", description=str(reason))
        return renderTemplate(
            "vnmk.html",
            session_timeout=SESSION_START_TIME + config.sessionTimeout
        )

    # ---- API for validating user identification + access code, then deciding
    #      whether to return or to destroy the stored credential.
    #      NOTICE that this API must be atomic, e.g. identification and access
    #      code MUST be provided in the same request. Only a single failure on
    #      identifying the user may be tolerated without destroying anything:
    #
    #      **with a valid user identification, access code must be validated
    #      before exiting this function!**

    @bottle.post("/<uid>/validate")
    def validate(uid):
        nonlocal SESSION_START_TIME
        if uid != config.userID: return bottle.abort(404)
        try:
            updateCredential()
        except Exception as reason:
            return jsonAnswer(error=str(reason))

        forms = bottle.request.json
        authdata = forms.get("auth")
        authcode = str(forms.get("code")).strip()

        # Step 1: Basic check
        if len(authcode) < 3:
            print("Access code too short.")
            return jsonAnswer(error="Access code too short.")

        # Step 2: Check id provider authentication.
        authResult = False
        authFailReason = None
        try:
            authResult = authenticator(authdata)
        except Exception as e:
            authResult = False
            authFailReason = str(e)
        if authResult == True:
            print("Authentication successful.")
        else:
            print("Authentication failed!", authFailReason)
            return jsonAnswer(error=authFailReason)

        # Step 3: Verification of access code
        if authcode == config.authCode:
            print("Access code valid. Releasing credential...")
            SESSION_START_TIME = -1 # reset countdown
            try:
                return jsonAnswer(result=config.releaseCredential())
            except Exception as e:
                print("Failed releasing credential. %s" % e)
                return jsonAnswer(error=str(e))
        else:
            print("Access code invalid. Destroy credential!")
            config.destroyCredential()
            return jsonAnswer(
                error="Credential destroyed due to invalid access code.")
        


    bottle.run(host=config.serverAddr, port=config.serverPort)
