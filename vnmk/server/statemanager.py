#!/usr/bin/env python3

import os
import time
import hashlib
import base64
import struct
from enum import Enum

import firebase_admin
from firebase_admin import credentials, db

from .config import ConfigFile
from .looptimer import LoopTimer

# TODO out-of-sync state may still happen due to temporialily network error.
# To overcome this, a special class maintaining(and enforce writing) new state
# creation time & new decayed mark time, shall be written.




class SystemState(Enum):
    # State cannot be determined/recorded reliably, e.g. due to network error.
    # By returning this state, the server shall lock down and not accept
    # any interaction.
    UNKNOWN = 0
    # Ground state
    GROUND   = 1
    # Excited state
    EXCITED  = 2
    # Decayed: ground or excited state timed out, credential should have been
    # destroyed.
    DECAYED  = 9

class StateUpdater:

    def __init__(self, userid, initState):
        self.userid = userid
        self.__internalState = initState
        self.__internalState["updated"] = time.time()
        self.__needSync = True 

    @property
    def creation(self):
        return self.__internalState["creation"]

    @property
    def updated(self):
        return self.__internalState["updated"]

    @property
    def excited(self):
        return self.__internalState["excited"]

    @property
    def decayed(self):
        return self.__internalState["decayed"]

    def set(self, key=None, value=None):
        assert key in ["creation", "excited", "decayed"]
        self.__internalState[key] = value
        self.__needSync = True

    def sync(self):
        try:
            if self.__needSync:
                print("Sync state to server...")
                nowtime = time.time()

                # TODO try to use multiprocessing for sync
                db.reference("/%s/" % self.userid).set({
                    "creation": self.__internalState["creation"],
                    "updated":  nowtime,
                    "excited":  self.__internalState["excited"],
                    "decayed":  self.__internalState["decayed"],
                })
                self.__internalState["updated"] = nowtime
                self.__needSync = False
        except Exception as e:
            print("Sync state error: %s" % e)


class StateManager:

    OUT_OF_SYNC_TOLERANCE = 300
    HEARTBEAT_INTERVAL    = 60
    TIMEOUT_GROUND        = 604800
    TIMEOUT_EXCITED       = 3600

    def __ref(self, *args):
        path = "/%s/" % self.userid + "/".join(args)
        return db.reference(path)

    @property
    def stateCreationTime(self):
        return self.stateUpdater.creation

    def __init__(self, config, creation=False):
        """Stores server status on disk."""
        assert isinstance(config, ConfigFile)
        self.userid = config.userID
        self.TIMEOUT_GROUND = config.groundStateTimeout
        self.TIMEOUT_EXCITED = config.excitedStateTimeout

        cred = credentials.Certificate(config.firebase["credential"])
        self.firebase = firebase_admin.initialize_app(cred, {
            "databaseURL": config.firebase["URL"],
            'databaseAuthVariableOverride': {
                'uid': '__python-server__'
            }
        })
        try:
            if creation:
                self.initDatabase()
                raise Exception(
                    "Database (re)initialized. " + \
                    "Please remove the --init option and run again.")
            else:
                initData = self.__ref().get()
                if not initData:
                    raise Exception(
                        "Data for this user does not exist. " +\
                        "Creation not allowed. Use --init option to run again."
                    )
                else:
                    self.stateUpdater = StateUpdater(self.userid, initData)
        except Exception as e:
            raise Exception(e)

    def initDatabase(self):
        print("Initialize database...")
        data = {        
            "creation": time.time(),
            "updated": time.time(),
            "excited": False,
            "decayed": False,
        }
        self.__ref().set(data)
        return data

    def createState(self, newState):
        """Creates an new state at remote server. Returns True if successes,
        otherwise False.
        """
        # NOTE this method SHALL be called before server may answer anything to
        # user. If this method fails, no record could be made.
        # TODO what if resuming from EXCITED to GROUND is temp. not possible?
        assert newState in [
            SystemState.EXCITED,
            SystemState.GROUND,
            SystemState.DECAYED
        ]
        if newState == SystemState.DECAYED:
            try:
                self.stateUpdater.set("decayed", True)
                self.stateUpdater.sync()
            except Exception as e:
                print("Cannot create new state: %s" % e)
            return True
        try:
            if self.stateUpdater.decayed:
                raise Exception("Server decayed. Cannot set new state.")
            nowtime = time.time()
            self.stateUpdater.set("excited", newState == SystemState.EXCITED)
            self.stateUpdater.set("creation", nowtime)
            self.stateUpdater.sync()
        except Exception as e:
            print("Cannot create new state: %s" % e)
            return False
        return True

    def recalculateState(self):
        """Recalculate server state. See if timed out!"""
        nowtime = time.time()
        creation = self.stateUpdater.creation
        excited  = self.stateUpdater.excited
        decayed  = self.stateUpdater.decayed
        if nowtime - self.stateUpdater.updated > self.OUT_OF_SYNC_TOLERANCE:
            print("State cannot be recalculated as server status outdated.")
            return SystemState.UNKNOWN
        if decayed:
            print("Server decayed!! State update stopped.")
            return SystemState.DECAYED
        if excited:
            timedout = ((nowtime - creation) > self.TIMEOUT_EXCITED)
        else:
            timedout = ((nowtime - creation) > self.TIMEOUT_GROUND)
        if timedout:
            self.stateUpdater.set("decayed", True)
            self.stateUpdater.sync()
            print("State timed out! Decay now!")
            return SystemState.DECAYED
        return SystemState.EXCITED if excited else SystemState.GROUND

    def heartbeat(self):
        """Check firebase server status."""
        print("Recalculate system state...")
        self.recalculateState()
        print("Sync with firebase server...")
        try:
            self.stateUpdater.sync()
        except Exception as e:
            print("Error in syncing: %s" % e)

        print(repr(self.reportState()))

    def reportState(self):
        try:
            return self.recalculateState()
        except Exception as e:
            print("Cannot determine system state. %s" % e)
            return SystemState.UNKNOWN

    def __enter__(self, *args):
        self.timer = LoopTimer(self.heartbeat, self.HEARTBEAT_INTERVAL)
        self.timer.start()
        return self

    def __exit__(self, *args):
        self.timer.stop()
