#!/usr/bin/env python3
import os

def serveAsFIFO(credential, filepath):
    if os.path.exists(filepath):
        os.unlink(filepath)

    while True:
        try:
            os.mkfifo(filepath)
            with open(filepath, "wb") as f:
                f.write(credential)
                f.flush()
                f.close()
            os.unlink(filepath)
        except KeyboardInterrupt as f:
            break
        except Exception as e:
            print(e)
            break
            continue

    os.unlink(filepath)
