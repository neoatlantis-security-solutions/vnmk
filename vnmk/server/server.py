#!/usr/bin/env python3

"""Use gevent for long polling AJAX"""
from gevent import monkey; monkey.patch_all()

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


HEADER_EXCITED_CSP = " ".join([
    "default-src",
    "'self'",
    "*.gstatic.com",
    "*.google.com",
    "*.firebase.com",
    "*.googleapis.com",
    "*.firebaseapp.com",
    "*.firebaseio.com",
    ";",
    "connect-src",
    "'self'",
    "wss://*.firebaseio.com",
    "https://*.googleapis.com",
])

HEADER_GROUND_CSP = " ".join([
    "default-src",
    "'self'",
])

def renderTemplate(filename, **arguments):
    fullname = fullpath("static", filename)
    return bottle.template(open(fullname, "r").read(), **arguments)

def jsonAnswer(error=None, result=None, relogin=None):
    return json.dumps({
        "error": error,
        "result": result,
        "relogin": relogin,
    })

def runServer(config, statemanager, telegram):
    assert isinstance(config, ConfigFile)
    authenticator = Authenticator(config)
    telegram.statemanager = statemanager

    def ensureServerState(*states, ensureCredential=True):
        currentState = statemanager.reportState()
        if currentState == SystemState.UNKNOWN:
            raise Exception("Server network error.")
        if currentState == SystemState.DECAYED:
            config.credential.destroy()
            raise Exception("Credential destroyed due to session timeout.")
        if currentState not in states:
            raise Exception("Please (re-)login with website UI.")
        if ensureCredential:
            # Ensure credential accessible & destroyable
            config.credential.ensure()
        return currentState

    # ---- Serves static files

    @bottle.get("/static/<filename>")
    def serveStatic(filename):
        return bottle.static_file(filename, root=fullpath("static"))

    # ---- Handles interface page for user login, which also includes starting
    #      the count down.

    @bottle.get("/<uid>/")
    def createSession(uid):
        if uid != config.userID: return bottle.abort(404)

        try:
            currentState = ensureServerState(
                SystemState.GROUND, SystemState.EXCITED,
                ensureCredential=False
            )
        except Exception as reason:
            return renderTemplate("error.html", description=str(reason))

        if currentState == SystemState.GROUND:
            bottle.response.set_header(
                "Content-Security-Policy",
                HEADER_GROUND_CSP
            )
            return renderTemplate(
                "activate.html",
                meta_csp=HEADER_GROUND_CSP,
                token=telegram.token
            )

        bottle.response.set_header(
            "Content-Security-Policy",
            HEADER_EXCITED_CSP
        )
        return renderTemplate(
            "vnmk.html",
            meta_csp=HEADER_EXCITED_CSP,
            user_id=config.userID,
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
    #      identifying the user may be tolerated without destroying anything.
    #
    #      **with a valid user identification, access code must be validated
    #      before exiting this function!**

    @bottle.post("/<uid>/validate")
    def validate(uid):
        if uid != config.userID: return bottle.abort(404)
        try:
            ensureServerState(SystemState.EXCITED)
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
            assert authdata["type"] == "firebase"
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
                customizedToken = config.firebase.issueCustomToken()
                return jsonAnswer(result={
                    "token": customizedToken,
                    "credential": config.credential.release()
                })
            except Exception as e:
                print("Failed releasing credential. %s" % e)
                return jsonAnswer(error=str(e))
        else:
            print("Access code invalid. Destroy credential!")
            statemanager.createState(SystemState.DECAYED)
            config.credential.destroy()
            return jsonAnswer(
                error="Credential destroyed due to invalid access code.")
        

    # ---- API for activating the system, e.g. turn it from ground state to
    #     excited state.

    """def activate(uid):
        if uid != config.userID: return bottle.abort(404)
        try:
            ensureServerState(SystemState.GROUND)
        except Exception as reason:
            return jsonAnswer(error=str(reason))

        query = bottle.request.query
        print(query)
        authdata = {"type": "telegram", "data": dict(query)}

        authResult = False
        authFailReason = None
        try:
            assert authdata["type"] == "telegram"
            authResult = authenticator(authdata)
        except Exception as e:
            authResult = False
            authFailReason = str(e)
        if authResult == True:
            print("Activation successful.")
            statemanager.createState(SystemState.EXCITED)
            return bottle.redirect("/%s/" % uid)
        else:
            print("Activation failed!", authFailReason)
            return renderTemplate("error.html", description=authFailReason)"""

    @bottle.get("/<uid>/activated")
    def activated(uid):
        if uid != config.userID: return bottle.abort(404)
        try:
            for i in range(0, 30):
                ensureServerState(SystemState.GROUND, ensureCredential=False)
                time.sleep(1)
        except Exception as reason:
            return jsonAnswer(result=True)
        return jsonAnswer(error=telegram.token, relogin=True)

    def onTokenVerified():
        try:
            ensureServerState(SystemState.GROUND) # prevent re-excitation
            statemanager.createState(SystemState.EXCITED)
        except Exception as e:
            print("Failed exciting system: %s" % e)
    telegram.onTokenVerified = onTokenVerified

    bottle.run(host=config.serverAddr, port=config.serverPort, server="gevent")
