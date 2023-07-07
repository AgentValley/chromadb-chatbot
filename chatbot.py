import os
from multiprocessing import Process
from time import time, sleep
from uuid import uuid4

import chromadb
import openai
from chromadb import Settings
from dotenv import load_dotenv

from cache.user_profile import get_user_profile, update_user_profile_in_db
from tools import KBCollection
from tools.load_data import load_data_from_urls
from utils import open_file, save_yaml, save_file, split_long_messages

load_dotenv()

MAX_TOKENS = 4000
SCRATCHPAD_LENGTH = 100
USER_SCRATCHPAD_LENGTH = 100

# instantiate ChromaDB
persist_directory = "_chromadb_"
chroma_client = chromadb.Client(Settings(persist_directory=persist_directory, chroma_db_impl="duckdb+parquet", ))

# instantiate chatbot
openai.api_key = os.getenv('OPENAI_API_KEY')
# conversation = list()


def chat_with_open_ai(conversation, model="gpt-3.5-turbo", temperature=0):
    max_retry = 3
    retry = 0
    messages = [{'role': x.get('role', 'assistant'),
                 'content': x.get('content', '')} for x in conversation]
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
            text = response['choices'][0]['message']['content']

            # trim message object
            debug_object = [i['content'] for i in messages]
            debug_object.append(text)
            save_yaml('api_logs/convo_%s.yaml' % time(), debug_object)
            if response['usage']['total_tokens'] >= MAX_TOKENS:
                messages = split_long_messages(messages)
                if len(messages) > 1:
                    messages.pop(1)

            return text
        except Exception as oops:
            print(f'Error communicating with OpenAI: "{oops}"')
            if 'maximum context length' in str(oops):
                messages = split_long_messages(messages)
                if len(messages) > 1:
                    messages.pop(1)
                print(' DEBUG: Trimming oldest message')
                continue
            retry += 1
            if retry >= max_retry:
                print(f"Exiting due to excessive errors in API: {oops}")
                return str(oops)
            print(f'Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)


def update_default_system(uid, current_profile, main_scratchpad, conversation):
    # search KB, update default system with main scratchpad

    kb = 'No KB articles yet'
    collection = KBCollection()
    # if collection.count() > 0:
    results = collection.query(query_texts=[main_scratchpad], n_results=1, where={"user": uid})
    kb = results['documents'][0][0]
    print('DEBUG: Found results %s' % results)
    default_system = open_file('chatbot_templates/system_default.txt'). \
        replace('<<PROFILE>>', current_profile) \
        .replace('<<KB>>', kb)

    print('SYSTEM: %s' % default_system)
    conversation[0]['content'] = default_system


def generate_response(conversation):
    response = chat_with_open_ai(conversation)
    # save_file('chat_logs/chat_%s_chatbot.txt' % time(), response)
    # conversation.append({'role': 'assistant', 'content': response})
    # all_messages.append('CHATBOT: %s' % response)
    print('CHATBOT: %s' % response)
    return response


def update_user_profile(uid, current_profile, user_scratchpad):
    print('Updating user profile...')
    profile_length = len(current_profile.split(' '))
    profile_conversation = list()
    content = open_file('chatbot_templates/system_update_user_profile.txt') \
        .replace('<<UPD>>', current_profile) \
        .replace('<<WORDS>>', str(profile_length))
    profile_conversation.append({'role': 'system',
                                 'content': content})
    profile_conversation.append({'role': 'user', 'content': user_scratchpad})
    profile = chat_with_open_ai(profile_conversation)

    # save_file('user_profile.txt', profile)
    print('====UPDATE PROFILE : [' + uid + ']==============')
    print(profile)
    update_user_profile_in_db(uid, profile)
    print('======================================')


def first_KB(uid, main_scratchpad):
    # yay first KB!
    kb_convo = list()
    kb_convo.append({'role': 'system', 'content': open_file('chatbot_templates/system_instantiate_new_kb.txt')})
    kb_convo.append({'role': 'user', 'content': main_scratchpad})
    article = chat_with_open_ai(kb_convo)
    new_id = str(uuid4())

    collection = KBCollection()
    print('====ARTICLE : [' + uid + ', ' + new_id + ']==============')
    print(article)
    print('=========================================================')
    collection.add(documents=[article], ids=[new_id], metadatas=[{'user': uid}])
    # save_file('db_logs/log_%s_add.txt' % time(), 'Added document %s:%s' % (new_id, article))


def update_KB(uid, main_scratchpad):
    collection = KBCollection()
    results = collection.query(query_texts=[main_scratchpad], n_results=1)
    print('update_KB DOCUMENTS:', results['documents'])
    if len(results['documents'][0]) > 0:
        kb = results['documents'][0][0]
        kb_id = results['ids'][0][0]
    else:
        kb = ""
        kb_id = ""
    if not kb_id:
        kb_id = str(uuid4())

    # Expand current KB
    kb_convo = list()
    kb_convo.append(
        {'role': 'system', 'content': open_file(
            'chatbot_templates/system_update_existing_kb.txt').replace('<<KB>>', kb)})
    kb_convo.append({'role': 'user', 'content': main_scratchpad})
    article = chat_with_open_ai(kb_convo)

    collection = KBCollection()
    print('====ARTICLE : [' + uid + ', ' + kb_id + ']==============')
    print(article)
    print('=========================================================')
    collection.update(ids=[kb_id], documents=[article], metadatas=[{'user': uid}])
    # save_file('db_logs/log_%s_update.txt' % time(), 'Updated document %s:%s' % (kb_id, article))
    # TODO - save more info in DB logs, probably as YAML file (original article, new info, final article)

    # Split KB if too large
    split_KB(kb_id, article)


def split_KB(kb_id, article):
    kb_len = len(article.split(' '))
    if kb_len > 1000:
        kb_convo = list()
        kb_convo.append({'role': 'system', 'content': open_file('chatbot_templates/system_split_kb.txt')})
        kb_convo.append({'role': 'user', 'content': article})
        articles = chat_with_open_ai(kb_convo).split('ARTICLE 2:')
        a1 = articles[0].replace('ARTICLE 1:', '').strip()
        a2 = articles[1].strip()

        collection = KBCollection()
        collection.update(ids=[kb_id], documents=[a1])
        new_id = str(uuid4())
        collection.add(documents=[a2], ids=[new_id])
        save_file('db_logs/log_%s_split.txt' % time(),
                  'Split document %s, added %s:%s\n%s' % (kb_id, new_id, a1, a2))


def generate_scratchpad(conversation):
    if len(conversation) > SCRATCHPAD_LENGTH:
        conversation.pop(0)
    scratchpad = '\n'.join(
        [x.get('role', '') + ' [' + x.get('time', '') + ']: ' + x.get('content', '') for x in conversation]).strip()
    return scratchpad


def pre_processing(uid, message, current_profile, conversation):
    print(f'Starting pre processing...')
    # get user input
    # all_messages.append('user: %s' % message)
    conversation.append({'role': 'user', 'content': message})
    # save_file(f'chat_logs/chat_%s_user-{user_id}.txt' % time(), message)

    # update default system with KB
    main_scratchpad = generate_scratchpad(conversation)

    update_default_system(uid, current_profile, main_scratchpad, conversation)
    print(f'Finished pre processing.')


def post_processing(uid, current_profile, conversation):
    print(f'Starting post processing...')

    user_messages = [x for x in conversation if x.get('role') == 'user']
    user_scratchpad = generate_scratchpad(user_messages)

    # update user profile
    update_user_profile(uid, current_profile, user_scratchpad)

    main_scratchpad = generate_scratchpad(conversation)

    # Update the knowledge base
    collection = KBCollection()
    if collection.count() == 0:
        print('Create first KB...')
        first_KB(uid, main_scratchpad)
    else:
        print('Updating KB...')
        update_KB(uid, main_scratchpad)

    chroma_client.persist()
    print(f'Finished post processing...')


def process_user_message(uid, cid, message, conversation):
    # current_profile = open_file('user_profile.txt')
    current_profile = get_user_profile(uid)

    # Extract urls from message and load data
    load_data_from_urls(uid, message, )

    if conversation:
        conversation.append({'role': 'system', 'content': open_file('chatbot_templates/system_default.txt')})
    # Prepare to generate response
    pre_processing(uid, message, current_profile, conversation)

    # generate a response
    response = generate_response(conversation)

    # Store the response
    post_process = Process(target=post_processing, args=(uid, current_profile, conversation,))
    post_process.start()

    return response
