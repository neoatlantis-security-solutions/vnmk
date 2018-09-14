#!/usr/bin/env python3

import bottle
import random
import os
import sys
import time
import json

from .config import ConfigFile
from .authenticator import Authenticator
from .statemanager import SystemState

BASEPATH = os.path.dirname(sys.argv[0])
fullpath = lambda *i: os.path.join(BASEPATH, *i)


HEADER_CSP = " ".join([
    "default-src",
    "'self'",
    "*.gstatic.com",
    "*.google.com",
    "*.firebase.com",
    "*.googleapis.com",
    "*.firebaseapp.com",
    "*.firebaseio.com"
])

def renderTemplate(filename, **arguments):
    fullname = fullpath("static", filename)
    return bottle.template(open(fullname, "r").read(), **arguments)

def jsonAnswer(error=None, result=None):
    return json.dumps({
        "error": error,
        "result": result, 
    })

def runServer(config, statemanager):
    assert isinstance(config, ConfigFile)
    authenticator = Authenticator(config)

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

    def ensureServerState():
        config.ensureCredential() # Ensure credential accessible & destroyable
        currentState = statemanager.reportState()
        if currentState == SystemState.UNKNOWN:
            raise Exception("Server network error.")
        if currentState == SystemState.DECAYED:
            config.destroyCredential()
            raise Exception("Credential destroyed due to session timeout.")
        return currentState


    # ---- Serves static files

    @bottle.get("/static/<filename>")
    def serveStatic(filename):
        return bottle.static_file(filename, root=fullpath("static"))

    # ---- Handles interface page for user login, which also includes starting
    #      the count down.

    randomIntentVerifier = RandomIntentVerifier()
    @bottle.get("/<uid>/")
    #@bottle.auth_basic(
    #    randomIntentVerifier,
    #    realm=randomIntentVerifier,
    #    text=randomIntentVerifier
    #)
    def createSession(uid):
        bottle.response.set_header("Content-Security-Policy", HEADER_CSP)

        if uid != config.userID:
            return renderTemplate(
                "error.html", 
                description="Invalid access URL."
            )
        try:
            currentState = ensureServerState()
        except Exception as reason:
            return renderTemplate("error.html", description=str(reason))
        
        if currentState == SystemState.GROUND:
            # Server turn into excited state!
            success = statemanager.createState(SystemState.EXCITED)
            if not success:
                # if failed exciting the server
                return renderTemplate(
                    "error.html",
                    description="Server network error."
                )
        return renderTemplate(
            "vnmk.html",
            meta_csp=HEADER_CSP,
            session_timeout=\
                statemanager.stateCreationTime + config.excitedStateTimeout,
            firebase_project_id=\
                config.firebaseConfig["credential"]["project_id"],
            firebase_api_key=config.idProviders["firebase"]["apikey"]
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
        if uid != config.userID: return bottle.abort(404)
        try:
            currentState = ensureServerState()
            if currentState != SystemState.EXCITED:
                raise Exception("Must login over Web UI.")
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
            return jsonAnswer(error=authFailReason, relogin=True)

        # Step 3: Verification of access code
        if authcode == config.authCode:
            print("Access code valid. Releasing credential...")
            try:
                statemanager.createState(SystemState.GROUND)
                return jsonAnswer(result=config.releaseCredential())
            except Exception as e:
                print("Failed releasing credential. %s" % e)
                return jsonAnswer(error=str(e))
        else:
            print("Access code invalid. Destroy credential!")
            statemanager.createState(SystemState.DECAYED)
            config.destroyCredential()
            return jsonAnswer(
                error="Credential destroyed due to invalid access code.")
        


    bottle.run(host=config.serverAddr, port=config.serverPort)
