#!/usr/bin/env python3

import threading

class LoopTimer:

    def __init__(self, func, interval=30):
        self.__func = func
        self.__interval = interval
        self.__timer = None

    def start(self):
        self.__onTicked()

    def __onTicked(self):
        self.__func()
        self.__timer = threading.Timer(self.__interval, self.__onTicked)
        self.__timer.start()

    def stop(self):
        if self.__timer:
            self.__timer.cancel()
