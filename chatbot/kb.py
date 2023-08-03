from uuid import uuid4

from logger import log_info
from tools import KBCollection
from tools.chat_openai import chat_with_open_ai
from tools.file import open_file


def first_KB(uid, main_scratchpad):
    # yay first KB!
    kb_convo = list()
    kb_convo.append({'role': 'system', 'content': open_file('chatbot_templates/system_instantiate_new_kb.txt')})
    kb_convo.append({'role': 'user', 'content': main_scratchpad})
    article = chat_with_open_ai(kb_convo)
    new_id = str(uuid4())

    collection = KBCollection(uid=uid)
    log_info('====ARTICLE : [' + uid + ', ' + new_id + ']==============')
    log_info(article)
    log_info('=========================================================')
    collection.add(documents=[article], ids=[new_id], metadatas=[{'user': uid}])
    KBCollection.persist()


def update_KB(uid, main_scratchpad):
    collection = KBCollection(uid=uid)
    results = collection.query(query_texts=[main_scratchpad], n_results=1)
    log_info('update_KB DOCUMENTS:', results['documents'])
    kb_id = None
    kb = ""
    if len(results['documents'][0]) > 0:
        kb = results['documents'][0][0]
        kb_id = results['ids'][0][0]

    # Expand current KB
    kb_convo = list()
    kb_convo.append(
        {'role': 'system', 'content': open_file(
            'chatbot_templates/system_update_existing_kb.txt').replace('<<KB>>', kb)})
    kb_convo.append({'role': 'user', 'content': main_scratchpad})
    article = chat_with_open_ai(kb_convo)
    log_info('====ARTICLE : [' + uid + ']==============')
    log_info(article)
    log_info('=========================================================')

    if not kb_id:
        kb_id = str(uuid4())
        collection.add(ids=[kb_id], documents=[article], metadatas=[{'user': uid}])
    else:
        collection.update(ids=[kb_id], documents=[article], metadatas=[{'user': uid}])

    KBCollection.persist()

    # Split KB if too large
    split_KB(uid, kb_id, article)


def split_KB(uid, kb_id, article):
    kb_len = len(article.split(' '))
    if kb_len > 1000:
        kb_convo = list()
        kb_convo.append({'role': 'system', 'content': open_file('chatbot_templates/system_split_kb.txt')})
        kb_convo.append({'role': 'user', 'content': article})
        articles = chat_with_open_ai(kb_convo).split('ARTICLE 2:')
        a1 = articles[0].replace('ARTICLE 1:', '').strip()
        a2 = articles[1].strip()

        collection = KBCollection(uid=uid)
        collection.update(ids=[kb_id], documents=[a1])
        new_id = str(uuid4())
        collection.add(documents=[a2], ids=[new_id])
        KBCollection.persist()
