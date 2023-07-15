import os
import requests

from cache.user_profile import UserProfileCache
from tools.chat_openai import chat_with_open_ai
from tools.file import open_file
from dotenv import load_dotenv

load_dotenv()


RECENT_MSGS_LENGTH = 5


def get_user_profile(uid, cid):
    if not uid or not cid:
        return ""

    user_profile = None
    try:
        user_profile = UserProfileCache.get(uid)
    except KeyError as e:
        print("ERROR get_user_profile", e)

    if not user_profile:
        url = f'{os.getenv("API_SERVER")}/room/profile?uid=' + uid + '&cid=' + cid + '&secret=' + os.getenv('SHARED_SECRET_KEY')
        response = requests.get(url)

        if response.status_code == 200:
            # Request successful
            user_profile = response.json().get('user_profile')
            # Cache the user profile
            try:
                UserProfileCache.set(uid, user_profile)
            except KeyError as e:
                print("ERROR get_user_profile", e)
        else:
            # Request failed
            print("ERROR get_user_profile", response.status_code, response.text)

    return user_profile


def update_user_profile(uid, cid, current_profile, recent_msgs=list()):

    try:
        template = open_file('chat_templates/user_profile_first.md')

        template = str(template)
        current_profile = str(current_profile)
        if recent_msgs:
            recent_msgs = "\n".join([x.get('content', '') for x in recent_msgs[-RECENT_MSGS_LENGTH:] if x.get('role') == 'user'])
        else:
            recent_msgs = ""

        conversation = [
            {'role': 'system', 'content': template},
            {'role': 'user', 'content': 'Use the details present in my current profile and return a UPD '
                                        ' User Profile Document by substituting the attributes. Remove those fields '
                                        'whose value is not available in current profile. '
                                        'USER PROFILE: ' + current_profile},
            {'role': 'user', 'content': 'Summarize the recent messages and append to the user profile resembling the'
                                        'progress made by the user. RECENT MESSAGES: ' + recent_msgs},
            {'role': 'user', 'content': 'If no profile data or conversation is provided. '
                                        'Then reply with generic student profile. Leave User Details and Contact '
                                        'as blank.'}
        ]
        user_profile = chat_with_open_ai(conversation)

        url = f'{os.getenv("API_SERVER")}/room/profile?secret=' + os.getenv('SHARED_SECRET_KEY')
        response = requests.post(url,
                                 json={"uid": uid, "cid": cid, "user_profile": user_profile},
                                 headers={'Content-Type': 'application/json'})

        if response.status_code == 200:
            # Request successful
            print(f"User profile updated")
        else:
            # Request failed
            print(f"GET request failed with status code: {response.status_code}")

        return user_profile
    except Exception as e:
        print("ERROR update_user_profile", e)
        return None


def update_system_profile(uid, cid, current_profile, recent_msgs=list()):
    try:
        template = open_file('chat_templates/system_profile_first.md')

        template = str(template)
        current_profile = str(current_profile)
        if recent_msgs:
            recent_msgs = "\n".join([x.get('content', '') for x in recent_msgs[-RECENT_MSGS_LENGTH:] if x.get('role') == 'assistant'])
        else:
            recent_msgs = ""

        conversation = [
            {'role': 'system', 'content': template},
            {'role': 'user', 'content': 'Use the details present in my current profile and return a system profile'
                                        'by substituting the attributes. Remove those fields who value is not '
                                        'available in current profile. Use this a reminder to yourself how to response'
                                        'to this user. SYSTEM PROFILE: ' + current_profile},
            {'role': 'user', 'content': 'Summarize the recent messages and append to the system profile resembling the'
                                        'progress made by the assistant. RECENT MESSAGES: ' + recent_msgs
                                         },
            {'role': 'system', 'content': 'If no profile data or conversation is provided. '
                                        'Then reply with generic tutor profile. Imagine you are teaching a random '
                                        'subject to the student by asking questions and giving explanations when '
                                        'the student is incorrect.'},
            {'role': 'system', 'content': 'Reply to the last user message and ask questions for clarity.'}
        ]
        system_profile = chat_with_open_ai(conversation)

        url = f'{os.getenv("API_SERVER")}/room/profile?secret=' + os.getenv('SHARED_SECRET_KEY')
        response = requests.post(url,
                                 json={"uid": uid, "cid": cid, "system_profile": system_profile},
                                 headers={'Content-Type': 'application/json'})

        if response.status_code == 200:
            # Request successful
            print(f"System profile updated")
        else:
            # Request failed
            print(f"GET request failed with status code: {response.status_code}")

        return system_profile
    except Exception as e:
        print("ERROR update_system_profile", e)
        return None


def update_profiles_to_db(uid, cid, user_profile, system_profile):
    if not uid or not cid:
        return

    url = f'{os.getenv("API_SERVER")}/room/profile?secret=' + os.getenv('SHARED_SECRET_KEY')
    response = requests.post(url,
                             json={"uid": uid, "cid": cid,
                                   "user_profile": user_profile,
                                   "system_profile": system_profile},
                             headers={'Content-Type': 'application/json'})

    if response.status_code == 200:
        # Request successful
        print(f"Updated user and system profiles to the db.")
    else:
        # Request failed
        print(f"GET request failed with status code: {response.status_code} {response.text}")
