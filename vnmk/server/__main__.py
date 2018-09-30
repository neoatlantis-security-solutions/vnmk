#!/usr/bin/env python3

import argparse
import yaml
import random
import os
import sys
import hashlib
import hmac
import time

from .server import runServer
from .initializer import initialize
from .config import ConfigFile
from .statemanager import StateManager
from .telegram import TelegramAuthenticateBot

parser = argparse.ArgumentParser()

parser.add_argument("config", action="store")
parser.add_argument(
    "--init", action="store", metavar="CREDENTIAL",
    help="""Use this option if running the server for the first time, or
    resetting the server from a previous decayed state into normal state. You
    have to provide the new credential that will be stored."""
)

args = parser.parse_args()

config = ConfigFile(args.config, initMode=bool(args.init))

with StateManager(config) as statemanager:
    if config.initMode:
        initialize(config, statemanager=statemanager, credentialPath=args.init)
    else:
        with TelegramAuthenticateBot(config.idProviders["telegram"]) as telegram:
            runServer(config, statemanager=statemanager, telegram=telegram)

"""
with\
    StateManager(config) as statemanager,\
    TelegramAuthenticateBot(config.idProviders["telegram"]) as telegram \
:
    if config.initMode:
        initialize(config, statemanager=statemanager, credentialPath=args.init)
    else:
        runServer(config, statemanager=statemanager, telegram=telegram)
"""
