#!/usr/bin/env python3

import subprocess
import time
import argparse

from .kiosk import getCredential

# ----------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    prog="python3 -m vnmk.client",
    description="""Client for accessing the VNMK(Volatile Non-Memorable Key)
    system.  You will be prompted with a browser to perform login. On success,
    the credential will be fetched by this client, providing further use."""
)

parser.add_argument(
    "--debug", help="Debug mode. Just DO NOT use this.", action="store_true")
parser.add_argument(
    "--not-gpg", help="Do not process the retrieved credential via GPG.",
    default=False,
    action="store_true"
)

args = parser.parse_args()

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
    credential = getCredential("test")

if not credential:
    print("Aborted.")
    exit()
else:
    credential = credential.encode("UTF-8")

# ----------------------------------------------------------------------------

if not args.not_gpg:

    process = subprocess.Popen(["gpg"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    credential = process.communicate(input=credential)[0]

    print(credential)
