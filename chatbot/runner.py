import os
from multiprocessing import Process

import chromadb
import openai
from chromadb import Settings
from dotenv import load_dotenv

from cache.user_profile import get_user_profile
from chatbot.profile import update_system_profile, update_user_profile
from tools.callback import update_profiles_to_db
from tools.chat_openai import chat_with_open_ai

load_dotenv()

MAX_TOKENS = 4000
SCRATCHPAD_LENGTH = 100
USER_SCRATCHPAD_LENGTH = 100

persist_directory = os.getenv("PERSIST_DIR", "../_chromadb_")
chroma_client = chromadb.Client(Settings(persist_directory=persist_directory, chroma_db_impl="duckdb+parquet", ))

openai.api_key = os.getenv('OPENAI_API_KEY')


def process_user_message(uid, cid, message, conversation):
    """
    LOGICAL STEPS TO TAKE:
    Collect data: user prompts and associated conversation history.

    Build ChromaDB index:Generate embeddings (vectors) for each prompt using ChromaDB.

    User query processing: Perform a similarity search against the prompt embeddings..

    System generation: Select the most relevant prompt to generate a system response.

    Integrate with ChatGPT: Obtain the response from ChatGPT.

    Provide the response: Incorporate the response into the conversation.
    """

    # Store the response
    # load_data_process = Process(target=load_data_from_urls, args=(uid, message, ))
    # load_data_process.start()

    current_user_profile = get_user_profile(uid)
    system_profile = update_system_profile(uid, cid, current_user_profile, conversation)

    if not conversation:
        conversation = [{'role': 'system', 'content': str(system_profile)}]
    else:
        conversation[0] = {'role': 'system', 'content': str(system_profile)}

    conversation.append({'role': 'user', 'content': message})

    response = chat_with_open_ai(conversation)
    user_profile = update_user_profile(uid, cid, current_user_profile, conversation)

    post_process = Process(target=update_profiles_to_db, args=(uid, cid, user_profile, system_profile,))
    post_process.start()

    # Store the response
    # post_process = Process(target=post_processing, args=(uid, current_profile, conversation,))
    # post_process.start()

    return response
