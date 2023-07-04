import os
from multiprocessing import Process
from time import time, sleep
from uuid import uuid4

import chromadb
import openai
from chromadb import Settings
from dotenv import load_dotenv

from cache.user_profile import get_user_profile, update_user_profile_in_db
from utils import open_file, save_yaml, save_file

load_dotenv()

MAX_TOKENS = 4000
SCRATCHPAD_LENGTH = 100
USER_SCRATCHPAD_LENGTH = 100

# instantiate ChromaDB
persist_directory = "_chromadb_"
chroma_client = chromadb.Client(Settings(persist_directory=persist_directory, chroma_db_impl="duckdb+parquet", ))
collection = chroma_client.get_or_create_collection(name="knowledge_base")

# instantiate chatbot
openai.api_key = os.getenv('OPENAI_API_KEY')
conversation = list()
conversation.append({'role': 'system', 'content': open_file('chatbot_templates/system_default.txt')})


def chatWithOpenAI(messages, model="gpt-3.5-turbo", temperature=0):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
            text = response['choices'][0]['message']['content']

            # trim message object
            debug_object = [i['content'] for i in messages]
            debug_object.append(text)
            save_yaml('api_logs/convo_%s.yaml' % time(), debug_object)
            if response['usage']['total_tokens'] >= MAX_TOKENS:
                messages.pop(1)

            return text
        except Exception as oops:
            print(f'\nError communicating with OpenAI: "{oops}"')
            if 'maximum context length' in str(oops):
                messages.pop(1)
                print('\n DEBUG: Trimming oldest message')
                continue
            retry += 1
            if retry >= max_retry:
                print(f"\nExiting due to excessive errors in API: {oops}")
                exit(1)
            print(f'\nRetrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)


def update_default_system(current_profile, main_scratchpad):
    # search KB, update default system with main scratchpad

    kb = 'No KB articles yet'
    if collection.count() > 0:
        results = collection.query(query_texts=[main_scratchpad], n_results=1)
        kb = results['documents'][0][0]
        print('\nDEBUG: Found results %s' % results)
    default_system = open_file('chatbot_templates/system_default.txt'). \
        replace('<<PROFILE>>', current_profile) \
        .replace('<<KB>>', kb)

    print('SYSTEM: %s' % default_system)
    conversation[0]['content'] = default_system


def generate_response():
    response = chatWithOpenAI(conversation)
    # save_file('chat_logs/chat_%s_chatbot.txt' % time(), response)
    # conversation.append({'role': 'assistant', 'content': response})
    # all_messages.append('CHATBOT: %s' % response)
    print('\nCHATBOT: %s' % response)
    return response


def update_user_profile(uid, current_profile, user_scratchpad):
    print('\nUpdating user profile...')
    profile_length = len(current_profile.split(' '))
    profile_conversation = list()
    content = open_file('chatbot_templates/system_update_user_profile.txt') \
        .replace('<<UPD>>', current_profile) \
        .replace('<<WORDS>>', str(profile_length))
    profile_conversation.append({'role': 'system',
                                 'content': content})
    profile_conversation.append({'role': 'user', 'content': user_scratchpad})
    profile = chatWithOpenAI(profile_conversation)

    # save_file('user_profile.txt', profile)
    update_user_profile_in_db(uid, profile)

def first_KB(uid, main_scratchpad):
    # yay first KB!
    kb_convo = list()
    kb_convo.append({'role': 'system', 'content': open_file('chatbot_templates/system_instantiate_new_kb.txt')})
    kb_convo.append({'role': 'user', 'content': main_scratchpad})
    article = chatWithOpenAI(kb_convo)
    new_id = str(uuid4())
    collection.add(documents=[article], ids=[new_id], metadatas=[{'user': uid}])
    # save_file('db_logs/log_%s_add.txt' % time(), 'Added document %s:\n%s' % (new_id, article))


def update_KB(uid, main_scratchpad):
    results = collection.query(query_texts=[main_scratchpad], n_results=1)
    print('\nupdate_KB DOCUMENTS:', results['documents'])
    if len(results['documents'][0]) > 0:
        kb = results['documents'][0][0]
        kb_id = results['ids'][0][0]
    else:
        kb = ""
        kb_id = ""

    # Expand current KB
    kb_convo = list()
    kb_convo.append(
        {'role': 'system', 'content': open_file(
            'chatbot_templates/system_update_existing_kb.txt').replace('<<KB>>', kb)})
    kb_convo.append({'role': 'user', 'content': main_scratchpad})
    article = chatWithOpenAI(kb_convo)
    if kb_id:
        collection.update(ids=[kb_id], documents=[article], metadatas=[{'user': uid}])
    else:
        collection.add(ids=[str(uuid4())], documents=[article], metadatas=[{'user': uid}])
    # save_file('db_logs/log_%s_update.txt' % time(), 'Updated document %s:\n%s' % (kb_id, article))
    # TODO - save more info in DB logs, probably as YAML file (original article, new info, final article)

    # Split KB if too large
    split_KB(kb_id, article)


def split_KB(kb_id, article):
    kb_len = len(article.split(' '))
    if kb_len > 1000:
        kb_convo = list()
        kb_convo.append({'role': 'system', 'content': open_file('chatbot_templates/system_split_kb.txt')})
        kb_convo.append({'role': 'user', 'content': article})
        articles = chatWithOpenAI(kb_convo).split('ARTICLE 2:')
        a1 = articles[0].replace('ARTICLE 1:', '').strip()
        a2 = articles[1].strip()
        collection.update(ids=[kb_id], documents=[a1])
        new_id = str(uuid4())
        collection.add(documents=[a2], ids=[new_id])
        save_file('db_logs/log_%s_split.txt' % time(),
                  'Split document %s, added %s:\n%s\n%s' % (kb_id, new_id, a1, a2))


def generate_scratchpad(_chat_history):
    if len(_chat_history) > SCRATCHPAD_LENGTH:
        _chat_history.pop(0)
    scratchpad = '\n'.join(
        [x.get('role') + '[' + x.get('time') + ']:' + x.get('content') for x in _chat_history]).strip()
    return scratchpad


def pre_processing(user_id, message, current_profile, chat_history):
    print(f'\nStarting pre processing...')
    # get user input
    # all_messages.append('user: %s' % message)
    conversation.append({'role': 'user', 'content': message})
    # save_file(f'chat_logs/chat_%s_user-{user_id}.txt' % time(), message)

    # update default system with KB
    main_scratchpad = generate_scratchpad(chat_history)

    update_default_system(current_profile, main_scratchpad)
    print(f'\nFinished pre processing.')


def post_processing(uid, current_profile, chat_history):
    print(f'\nStarting post processing...')

    user_messages = [x for x in chat_history if x.get('role') == 'user']
    user_scratchpad = generate_scratchpad(user_messages)

    # update user profile
    update_user_profile(uid, current_profile, user_scratchpad)

    main_scratchpad = generate_scratchpad(chat_history)

    # Update the knowledge base
    print('\nUpdating KB...')
    if collection.count() == 0:
        first_KB(uid, main_scratchpad)
    else:
        update_KB(uid, main_scratchpad)

    chroma_client.persist()
    print(f'\nFinished post processing...')


def process_user_message(uid, course_name, message, chat_history):
    # current_profile = open_file('user_profile.txt')
    current_profile = get_user_profile(uid)

    # Prepare to generate response
    pre_processing(uid, message, current_profile, chat_history)

    # generate a response
    response = generate_response()

    # Store the response
    post_process = Process(target=post_processing, args=(uid, current_profile, chat_history,))
    post_process.start()

    return response
