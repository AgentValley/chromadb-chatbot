import os
from multiprocessing import Process

import chromadb
import openai
from chromadb import Settings


from chatbot.post_chat import post_processing
from chatbot.profile import update_system_profile, update_user_profile, get_user_profile, update_profiles_to_db
from logger import log_info
from tools.chat_openai import chat_with_open_ai
from dotenv import load_dotenv

load_dotenv()

MAX_TOKENS = 4000
SCRATCHPAD_LENGTH = 100
USER_SCRATCHPAD_LENGTH = 100


openai.api_key = os.getenv('OPENAI_API_KEY')


def process_user_message(uid, cid, message, conversation):
    log_info('Start process user message', uid, cid, message, conversation)
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

    current_user_profile = get_user_profile(uid, cid)
    system_profile = update_system_profile(uid, cid, current_user_profile, conversation)

    if not conversation:
        conversation = [{'role': 'system', 'content': str(system_profile)}]
    else:
        conversation[0] = {'role': 'system', 'content': str(system_profile)}

    conversation.append({'role': 'user', 'content': str(message)})

    response = chat_with_open_ai(conversation)
    user_profile = update_user_profile(uid, cid, current_user_profile, conversation)

    post_process = Process(target=update_profiles_to_db, args=(uid, cid, user_profile, system_profile,))
    post_process.start()

    # Store the response
    # post_process = Process(target=post_processing, args=(uid, current_user_profile, conversation,))
    # post_process.start()

    return response
