import os
import requests

from cachetools import TTLCache

from utils import open_file

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
        url = f'http://{os.getenv("API_SERVER")}/user/profile?uid=' + uid
        response = requests.get(url)

        if response.status_code == 200:
            # Request successful
            user_profile = response.json().get('user_profile')
            if not user_profile:
                user_profile = open_file('user_profile.txt')

            # Cache the user profile
            try:
                UserProfileCache.set(uid, user_profile)
            except KeyError as e:
                print(str(e))
        else:
            # Request failed
            print(f"GET request failed with status code: {response.status_code}")

    return user_profile


def update_user_profile_in_db(uid, user_profile):
    if not uid or not user_profile:
        return

    url = f'http://{os.getenv("API_SERVER")}/user/profile'
    response = requests.post(url, json={"uid": uid, "user_profile": user_profile}, headers={'Content-Type': 'application/json'})

    if response.status_code == 200:
        # Request successful
        print(f"User profile updated")
    else:
        # Request failed
        print(f"GET request failed with status code: {response.status_code}")

    # Cache the user profile
    try:
        UserProfileCache.set(uid, user_profile)
    except KeyError as e:
        print(str(e))
