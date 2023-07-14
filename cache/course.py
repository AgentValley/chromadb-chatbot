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


def get_course(cid):
    if not cid:
        return
    # Check if courses are available in the cache
    course = None
    try:
        course = CourseCache.get(cid)
    except KeyError as e:
        print("ERROR get_course", e)

    if not course:
        # Fetch courses from MongoDB for the user
        url = f'{os.getenv("API_SERVER")}/course?cid=' + cid
        response = requests.get(url)

        if response.status_code == 200:
            # Request successful
            course = response.json()
            # Cache the courses
            try:
                CourseCache.set(cid, course)
            except KeyError as e:
                print("ERROR get_course", e)
        else:
            # Request failed
            print(f"GET request failed with status code: {response.status_code} {response.text}")
            print(f"Response", response)
            return None

    return course
