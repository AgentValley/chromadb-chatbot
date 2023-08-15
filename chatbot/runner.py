import os

import openai
from dotenv import load_dotenv

from chatbot.profile import get_user_and_system_profile, generate_new_system_profile
from logger import log_debug
from tools.chat_openai import chat_with_open_ai

load_dotenv()

MAX_TOKENS = 4000
SCRATCHPAD_LENGTH = 100
USER_SCRATCHPAD_LENGTH = 100

openai.api_key = os.getenv('OPENAI_API_KEY')


def process_user_message(uid, cid, message, conversation):
    log_debug(f'Processing User Message: ({uid}) ({cid}) {message}')
    """
    LOGICAL STEPS TO TAKE:
    1. Collect data: user prompts and associated conversation history.
    2. Build ChromaDB index:Generate embeddings (vectors) for each prompt using ChromaDB.
    3. User query processing: Perform a similarity search against the prompt embeddings.
    4. System generation: Select the most relevant prompt to generate a system response.
    5. Integrate with ChatGPT: Obtain the response from ChatGPT.
    6. Provide the response: Incorporate the response into the conversation.
    """

    # Store the response
    # load_data_process = Process(target=load_data_from_urls, args=(uid, message, ))
    # load_data_process.start()

    # user_profile, system_profile = get_user_and_system_profile(uid, cid)
    # log_debug(f'Got Profiles: \nUser Profile: {user_profile[:20]}\nSystem Profile: {system_profile}')

    # system_profile = generate_new_system_profile(uid, cid, conversation, user_profile, system_profile)
    # log_debug(f'Updated System Profile: \n{system_profile[:20]}')

    # if not conversation:
    #     conversation = [{'role': 'system', 'content': str(system_profile)}]
    # else:
    #     conversation[0] = {'role': 'system', 'content': str(system_profile)}

    conversation.append({'role': 'user', 'content': str(message)})

    response = chat_with_open_ai(conversation)

    """
    user_profile = update_user_profile(uid, cid, current_user_profile, conversation)

    post_process = Process(target=update_profiles_to_db, args=(uid, cid, user_profile, system_profile,))
    post_process.start()
    """

    # Store the response
    # post_process = Process(target=post_processing, args=(uid, current_user_profile, conversation,))
    # post_process.start()

    log_debug(f'Got Response:  ({uid}) ({cid}) {response}')
    return response
