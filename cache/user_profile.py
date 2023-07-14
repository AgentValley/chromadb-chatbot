import os
import requests

from cachetools import TTLCache
from dotenv import load_dotenv

load_dotenv()


MAX_CONVO_LENGTH = 100


class UserProfileCache(object):  # Singleton
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = TTLCache(maxsize=200, ttl=36000)
        return cls._instance

    @staticmethod
    def get(key):
        if not UserProfileCache._instance:
            UserProfileCache()
        return UserProfileCache._instance.get(key)

    @staticmethod
    def set(key, data):
        if not UserProfileCache._instance:
            UserProfileCache()
        UserProfileCache._instance[key] = data
