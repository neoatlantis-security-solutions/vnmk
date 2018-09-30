#!/usr/bin/env python3

import os
import time
import hashlib
import base64
import struct
from enum import Enum
from multiprocessing import Process

import firebase_admin
from firebase_admin import credentials, db

from .config import ConfigFile
from .looptimer import LoopTimer



class SystemState(Enum):
    # Initialization mode, the user is allowed to upload credential to
    # firebase server.
    INIT = -1
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



class StateUpdater(LoopTimer):

    INTERVAL = 30

    def __init__(self, userid, initState):
        self.userid = userid
        self.__internalState = initState
        self.__internalState["updated"] = time.time()
        self.__needSync = True
        self.__syncProcess = None
        LoopTimer.__init__(self, self.__sync, self.INTERVAL)

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

    def __syncWriteProcess(self, newState, newTime):
        try:
            print("---- Sync new state...")
            newState["updated"] = newTime
            db.reference("/state/%s/" % self.userid).set(newState)
            return exit(0)
        except Exception as e:
            print("---- Sync error: %s" % e)
            return exit(1)

    def __sync(self):
        """NOTE this should be called within another thread, periodically."""
        nowtime = time.time()
        # check for last sync
        if self.__syncProcess:
            if self.__syncProcess.exitcode == None:
                self.__syncProcess.terminate()
                print("---- Sync timed out.")
            elif self.__syncProcess.exitcode == 0:
                self.__internalState["updated"] = self.__syncProcess._updated
                print("---- Sync ended successfully: %d." %\
                    self.__internalState["updated"])
        # do next sync
        if not self.__needSync: return
        self.__syncProcess = Process(
            target=self.__syncWriteProcess,
            args=(self.__internalState, nowtime)
        )
        setattr(self.__syncProcess, "_updated", nowtime)
        self.__syncProcess.start()

    def stop(self):
        if self.__syncProcess and self.__syncProcess.exitcode == None:
            self.__syncProcess.terminate()
        LoopTimer.stop(self)



class StateManager:

    OUT_OF_SYNC_TOLERANCE = 120
    HEARTBEAT_INTERVAL    = 15 
    TIMEOUT_GROUND        = 604800
    TIMEOUT_EXCITED       = 3600

    def __ref(self, *args):
        path = "/state/%s/" % self.userid + "/".join(args)
        return db.reference(path)

    @property
    def stateCreationTime(self):
        return self.stateUpdater.creation

    def __init__(self, config):
        """Stores server status on disk."""
        assert isinstance(config, ConfigFile)
        self.config = config
        self.userid = config.userID
        self.TIMEOUT_GROUND = config.groundStateTimeout
        self.TIMEOUT_EXCITED = config.excitedStateTimeout

        self.firebase = config.firebase
        try:
            if config.initMode:
                self.stateUpdater = StateUpdater(
                    self.userid, initState=self.initDatabase())
            else:
                initState = self.__ref().get()
                if not initState:
                    raise Exception(
                        "Data for this user does not exist. " +\
                        "Creation not allowed. Use --init option to run again."
                    )
                else:
                    self.stateUpdater = StateUpdater(self.userid, initState)
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
        if self.config.initMode:
            raise Exception("Cannot create new state in INIT mode.")
        assert newState in [
            SystemState.EXCITED,
            SystemState.GROUND,
            SystemState.DECAYED
        ]
        if newState == SystemState.DECAYED:
            try:
                self.stateUpdater.set("decayed", True)
            except Exception as e:
                print("Cannot create new state: %s" % e)
            return True
        try:
            if self.stateUpdater.decayed:
                raise Exception("Server decayed. Cannot set new state.")
            nowtime = time.time()
            self.stateUpdater.set("excited", newState == SystemState.EXCITED)
            self.stateUpdater.set("creation", nowtime)
        except Exception as e:
            print("Cannot create new state: %s" % e)
            return False
        return True

    def recalculateState(self):
        """Recalculate server state. See if timed out!"""
        if self.config.initMode: return SystemState.INIT
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
            print("State timed out! Decay now!")
            return SystemState.DECAYED
        return SystemState.EXCITED if excited else SystemState.GROUND

    def heartbeat(self):
        """Check firebase server status."""
        print("Recalculate system state...")
        self.recalculateState()
        print("System state: ", repr(self.reportState()))

    def reportState(self):
        try:
            return self.recalculateState()
        except Exception as e:
            print("Cannot determine system state. %s" % e)
            return SystemState.UNKNOWN

    def __enter__(self, *args):
        if self.config.initMode: return self
        self.timer = LoopTimer(self.heartbeat, self.HEARTBEAT_INTERVAL)
        self.timer.start()
        self.stateUpdater.start()
        return self

    def __exit__(self, *args):
        if self.config.initMode: return
        self.timer.stop()
        self.stateUpdater.stop()
