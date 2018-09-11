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
from .config import ConfigFile
from .statemanager import StateManager

parser = argparse.ArgumentParser()

parser.add_argument("config", action="store")
parser.add_argument(
    "--init", action="store_true",
    help="Use this option if running the server for the first time."
)

args = parser.parse_args()

config = ConfigFile(args.config)

with StateManager(config, creation=args.init) as statemanager:
    runServer(config, statemanager=statemanager)
