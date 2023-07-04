import os
import requests
from datetime import datetime

from cachetools import TTLCache


MAX_CONVO_LENGTH = 100


class CourseCache(object):  # Singleton
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = TTLCache(maxsize=200, ttl=36000)
        return cls._instance

    @staticmethod
    def get(key):
        if not CourseCache._instance:
            CourseCache()
        return CourseCache._instance.get(key)

    @staticmethod
    def set(key, data):
        if not CourseCache._instance:
            CourseCache()
        CourseCache._instance[key] = data


def get_course(name):
    if not name:
        return
    # Check if courses are available in the cache
    course = None
    try:
        course = CourseCache.get(name)
    except KeyError as e:
        print(e)

    if not course:
        # Fetch courses from MongoDB for the user
        url = f'http://{os.getenv("API_SERVER")}/user/profile'
        response = requests.get(url)

        if response.status_code == 200:
            # Request successful
            course = response.json()
            # Cache the courses
            try:
                CourseCache.set(name, course)
            except KeyError as e:
                print(str(e))
        else:
            # Request failed
            print(f"GET request failed with status code: {response.status_code}")
            return None

    return course
