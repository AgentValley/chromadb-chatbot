import os

import requests


def update_profiles_to_db(uid, cid, user_profile, system_profile):
    if not uid or not cid:
        return

    url = f'{os.getenv("API_SERVER")}/course/profile'
    response = requests.post(url,
                             json={"uid": uid, "cid": cid,
                                   "user_profile": user_profile,
                                   "system_profile": system_profile},
                             headers={'Content-Type': 'application/json'})

    if response.status_code == 200:
        # Request successful
        print(f"User profile updated")
    else:
        # Request failed
        print(f"GET request failed with status code: {response.status_code}")
