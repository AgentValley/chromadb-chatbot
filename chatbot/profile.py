import os
from multiprocessing import Process

import requests
from dotenv import load_dotenv

from logger import log_info, log_error, log_warn
from tools.chat_openai import chat_with_open_ai
from tools.file import open_file

load_dotenv()

RECENT_MSGS_LENGTH = 5


def get_user_and_system_profile(uid, cid):
    if not uid or not cid:
        return "", ""

    # key = f'{uid}-{cid}'
    # try:
    #     user_profile = UserProfileCache.get(key)
    # except KeyError as e:
    #     log_error(f'Failed to get user profile from cache {e}')

    url = (f'{os.getenv("API_SERVER")}/room/profile?'
           'uid=' + uid +
           '&cid=' + cid +
           '&secret=' + os.getenv('SHARED_SECRET_KEY'))
    response = requests.get(url)

    if response.status_code == 200:
        # Request successful
        user_profile = response.json().get('user_profile')
        system_profile = response.json().get('system_profile')
        # Cache the user profile
        # try:
        #     UserProfileCache.set(key, user_profile)
        # except KeyError as e:
        #     log_warn(f"Error getting user profile from cache {e}")
    else:
        # Request failed
        log_warn(f"Error getting user profile from cache {response.status_code} {response.text}")
        user_profile, system_profile = "", ""

    return user_profile, system_profile


def update_user_profile(uid, cid, current_profile, recent_msgs=list()):
    try:
        template = open_file('chat_templates/user_profile_first.md')

        template = str(template)
        current_profile = str(current_profile)
        if recent_msgs:
            recent_msgs = "\n".join(
                [x.get('content', '') for x in recent_msgs[-RECENT_MSGS_LENGTH:] if x.get('role') == 'user'])
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
            log_info(f"User profile updated")
        else:
            # Request failed
            log_info(f"GET request failed with status code: {response.status_code}")

        return user_profile
    except Exception as e:
        log_error(f'Failed to update user profile {e}')
        return None


def generate_new_system_profile(uid, cid, recent_msgs, user_profile, system_profile):
    try:
        template = open_file('chat_templates/system_profile_first.md')

        template = str(template)
        recent_assistant_msgs = ""
        recent_user_msgs = ""
        if recent_msgs:
            recent_assistant_msgs = "\n".join(
                [x.get('content', '') for x in recent_msgs[-RECENT_MSGS_LENGTH:] if x.get('role') == 'assistant'])
            recent_user_msgs = "\n".join(
                [x.get('content', '') for x in recent_msgs[-RECENT_MSGS_LENGTH:] if x.get('role') == 'user'])

        conversation = [
            {'role': 'system', 'content': template},
            {'role': 'system', 'content': 'This is current user profile. User this info to know about the user, '
                                          'their progress and preferences. Given following data: '
                                          f'USER PROFILE>>> {user_profile}'
                                          f'USER MESSAGES >>> {recent_user_msgs}'
                                          f'ASSISTANT MESSAGES >>> {recent_assistant_msgs}'
                                          f'SYSTEM PROFILE >>> {system_profile}'
                                          f''
                                          f'If no profile data or conversation is provided. Stick to the goal'
                                          f'Analyze the whole context and return the instructions for the AI Tutor'
                                          f'on how to proceed. Some default options are start learning, '
                                          f'choosing a topic, do some exercises, etc. Include course name and goal.'}
        ]
        system_profile = chat_with_open_ai(conversation)

        process = Process(target=update_system_profile, args=(uid, cid, system_profile))
        process.start()

        return system_profile

    except Exception as e:
        log_error(f'Failed to generate system profile ❌ :: {uid} ({cid}) :: {e}')
        return None


def update_system_profile(uid, cid, system_profile):
    url = f'{os.getenv("API_SERVER")}/room/profile?secret=' + os.getenv('SHARED_SECRET_KEY')
    response = requests.post(url,
                             json={"uid": uid, "cid": cid, "system_profile": system_profile},
                             headers={'Content-Type': 'application/json'})

    if response.status_code == 200:
        # Request successful
        log_info(f'System profile updated ✅ {uid} ({cid}) :: {system_profile}')
    else:
        # Request failed
        log_info(f'Failed to update system profile ❌ {uid} ({cid}) :: {response.text}')


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
        log_info('User and system profiles updated.')
    else:
        # Request failed
        log_info('User and system profiles updated.', response)
