#!/usr/bin/env python3

import subprocess

def GPGDecrypt(filename):
    ret = subprocess.check_output(["gpg", "--decrypt", filename])
    return ret.decode("utf-8")
