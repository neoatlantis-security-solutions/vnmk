#!/usr/bin/env python3

import argparse
import yaml
import random
import os
import sys
import hashlib
import hmac
import time

import firebase_admin
from firebase_admin import auth

from .config import ConfigFile



class Authenticator:
    
    TIMEOUT = 300

    def __init__(self, config):
        assert isinstance(config, ConfigFile)
        self.idProviders = config.idProviders
        self.DEBUG = config.DEBUG
        #self.__firebase = config.firebase

    def __call__(self, data):
        method = data["type"]
        data = data["data"]
        if not hasattr(self, method) or method not in self.idProviders:
            raise Exception("Authentication method %s not supported." % method) 
        if self.DEBUG:
            print("**** WARNING: DEBUG=True SET. ****")
            return True
        return getattr(self, method)(self.idProviders[method], data)

    # ---- Telegram Authentication

    def telegram(self, config, data):
        key = hashlib.sha256(config["token"].encode("utf-8")).digest()

        try:
            authTime = int(data["auth_date"])
            if abs(time.time() - authTime) > self.TIMEOUT:
                raise Exception(
                    "Authentication timestamp invalid. " + \
                    "Try re-login or fix server time.")
        except Exception as e:
            raise e 

        try:
            # make sure user is allowed
            if data["username"] not in config["users"]:
                raise Exception("User is not allowed to access.")
        except Exception as e:
            raise e
        
        try:
            dataKeys = sorted(data.keys())
            dataCheckStr = "\n".join([
                "%s=%s" % (key, data[key]) for key in dataKeys if key != "hash"
            ]).encode("utf-8")
            dataCheckHash = data["hash"]
            calcCheckHash = hmac.new(
                key, dataCheckStr, hashlib.sha256).hexdigest()
            assert dataCheckHash == calcCheckHash
        except:
            raise Exception("Malformed authentication request.")

        return True


    # ---- Firebase Authentication

    def firebase(self, config, data):
        """{
            'iss': 'https://securetoken.google.com/...',
            'name': '...',
            'picture': '...', 'aud': '...', 'auth_time': 1536947307,
            'user_id': '...', 'sub': '...', 'iat': 1536947882, 'exp': 1536951482,
            'email': '...',
            'email_verified': False,
            'uid': '...'
        }"""
        decodedToken = auth.verify_id_token(data)
        if "one-time-token" in config and config["one-time-token"] == True:
            # Feature: token may used only once.
            auth.revoke_refresh_tokens(decodedToken["uid"])
        if abs(time.time() - decodedToken["auth_time"]) > self.TIMEOUT:
            raise Exception("Token timed out. Relogin required.")
        if not decodedToken["email"] in config["users"]:
            raise Exception("User is not allowed to access.")
        return True
