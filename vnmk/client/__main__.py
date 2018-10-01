#!/usr/bin/env python3

import subprocess
import time
import argparse
import os

from .kiosk import getCredential
from.actions.fifo import serveAsFIFO

# ----------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    prog="python3 -m vnmk.client",
    description="""Client for accessing the VNMK(Volatile Non-Memorable Key)
    system.  You will be prompted with a browser to perform login. On success,
    the credential will be fetched by this client, providing further use."""
)

parser.add_argument(
    "user_id", metavar="USER_ID", help="Your user id at remote location.")

parser.add_argument(
    "--debug", help="Debug mode. Just DO NOT use this.", action="store_true")
parser.add_argument(
    "--not-gpg", help="Do not process the retrieved credential via GPG.",
    default=False,
    action="store_true"
)

actions = parser.add_mutually_exclusive_group(required=True)
actions.add_argument("--as-file", metavar="FILE")


# ----------------------------------------------------------------------------

args = parser.parse_args()

if args.as_file and os.path.exists(args.as_file):
    print("Error: [%s] exists. Cannot serve at that location." % args.as_file)
    exit(1)

# ----------------------------------------------------------------------------

DEBUG = args.debug
if DEBUG:
    # test credential, pwd is "test"
    credential = """
-----BEGIN PGP MESSAGE-----

jA0ECQMC3YYeMaM0Q8//0mwBKadpgShyPglyGBUhFqs21eU/AXqJcco6fOhwb7AH
FA0888lyFsy2PM/4qlTW9w9bHdfNSN471Wovi2sQ8bz0lCZJuJfmqk3R4cypZgBa
PXSHr/PR9odA2ehtIxhnr35V9silSoes7w49y4Q=
=dMqL
-----END PGP MESSAGE-----
        """
else:
    credential = getCredential(args.user_id)

if not credential:
    print("Aborted.")
    exit()
else:
    credential = credential.encode("UTF-8")

# ----------------------------------------------------------------------------

if not args.not_gpg:

    process = subprocess.Popen(["gpg"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    credential = process.communicate(input=credential)[0]

assert type(credential) == bytes

if args.as_file:
    serveAsFIFO(credential, args.as_file)
