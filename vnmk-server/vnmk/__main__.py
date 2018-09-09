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

runServer(ConfigFile("test.yaml"))

##############################################################################

parser = argparse.ArgumentParser()

argMode = parser.add_mutually_exclusive_group(required=True)
argMode.add_argument("-s", "--serve", metavar="CONFIG FILE", action="store")
argMode.add_argument(
    "-i", "--init", metavar="CREDENTIAL", action="store",
    help="Generates a new config file containing given credential."
)

parser.parse_args()


