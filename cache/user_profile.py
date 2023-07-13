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


def get_user_profile(uid):
    if not uid:
        return ""

    user_profile = None
    try:
        user_profile = UserProfileCache.get(uid)
    except KeyError as e:
        print(str(e))

    if not user_profile:
        url = f'{os.getenv("API_SERVER")}/user/profile?uid=' + uid + '&secret=' + os.getenv('SHARED_SECRET_KEY')
        response = requests.get(url)

        if response.status_code == 200:
            # Request successful
            user_profile = response.json().get('user_profile')
            # Cache the user profile
            try:
                UserProfileCache.set(uid, user_profile)
            except KeyError as e:
                print(str(e))
        else:
            # Request failed
            print(f"GET request failed with status code: {response.status_code}")

    return user_profile

