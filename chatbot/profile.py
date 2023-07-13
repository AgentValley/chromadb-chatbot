import os
import requests

from tools.chat_openai import chat_with_open_ai
from tools.file import open_file


RECENT_MSGS_LENGTH = 5


def update_user_profile(uid, cid, current_profile, recent_msgs=[]):
    try:
        template = open_file('chat_templates/user_profile_first.md')

        conversation = [
            {'role': 'system', 'content': template},
            {'role': 'user', 'content': 'Use the details present in my current profile and return a UPD '
                                        ' User Profile Document by substituting the attributes. Remove those fields '
                                        'whose value is not available in current profile. '
                                        'USER PROFILE: ' + current_profile},
            {'role': 'user', 'content': 'Summarize the recent messages and append to the user profile resembling the'
                                        'progress made by the user. RECENT MESSAGES: ' +
                                        "\n".join([x.get('content', '') for x in recent_msgs[-RECENT_MSGS_LENGTH:] if x.get('role') == 'user'])}
        ]
        user_profile = chat_with_open_ai(conversation)

        url = f'{os.getenv("API_SERVER")}/room/profile'
        response = requests.post(url,
                                 json={"uid": uid, "cid": cid, "user_profile": user_profile},
                                 headers={'Content-Type': 'application/json'})

        if response.status_code == 200:
            # Request successful
            print(f"User profile updated")
        else:
            # Request failed
            print(f"GET request failed with status code: {response.status_code}")

        return response
    except Exception as e:
        print(e)
        return None


def update_system_profile(uid, cid, current_profile, recent_msgs):
    try:
        # kb = 'No KB articles yet'
        # collection = KBCollection(uid=uid)
        # # if collection.count() > 0:
        # results = collection.query(query_texts=[query_texts])
        #
        # if len(results['documents'][0]) > 0:
        #     kb = results['documents'][0][0]
        # print('DEBUG: Found results %s' % results)

        template = open_file('chat_templates/system_profile_first.md')

        conversation = [
            {'role': 'system', 'content': template},
            {'role': 'user', 'content': 'Use the details present in my current profile and return a system profile'
                                        'by substituting the attributes. Remove those fields who value is not '
                                        'available in current profile. Use this a reminder to yourself how to response'
                                        'to this user. SYSTEM PROFILE: ' + current_profile},
            {'role': 'user', 'content': 'Summarize the recent messages and append to the system profile resembling the'
                                        'progress made by the assistant. RECENT MESSAGES: ' +
                                         "\n".join([x.get('content', '') for x in recent_msgs[-RECENT_MSGS_LENGTH:] if x.get('role') == 'assistant'])}
        ]
        system_profile = chat_with_open_ai(conversation)

        url = f'{os.getenv("API_SERVER")}/room/profile'
        response = requests.post(url,
                                 json={"uid": uid, "cid": cid, "system_profile": system_profile},
                                 headers={'Content-Type': 'application/json'})

        if response.status_code == 200:
            # Request successful
            print(f"System1 profile updated")
        else:
            # Request failed
            print(f"GET request failed with status code: {response.status_code}")

        return response
    except Exception as e:
        print(e)
        return None
