


def first_KB(uid, main_scratchpad):
    # yay first KB!
    kb_convo = list()
    kb_convo.append({'role': 'system', 'content': open_file('chatbot_templates/system_instantiate_new_kb.txt')})
    kb_convo.append({'role': 'user', 'content': main_scratchpad})
    article = chat_with_open_ai(kb_convo)
    new_id = str(uuid4())

    collection = KBCollection(uid=uid)
    print('====ARTICLE : [' + uid + ', ' + new_id + ']==============')
    print(article)
    print('=========================================================')
    collection.add(documents=[article], ids=[new_id], metadatas=[{'user': uid}])
    KBCollection.persist()
    # save_file('db_logs/log_%s_add.txt' % time(), 'Added document %s:%s' % (new_id, article))


def update_KB(uid, main_scratchpad):
    collection = KBCollection(uid=uid)
    results = collection.query(query_texts=[main_scratchpad], n_results=1)
    print('update_KB DOCUMENTS:', results['documents'])
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
    print('====ARTICLE : [' + uid + ']==============')
    print(article)
    print('=========================================================')

    if not kb_id:
        kb_id = str(uuid4())
        collection.add(ids=[kb_id], documents=[article], metadatas=[{'user': uid}])
    else:
        collection.update(ids=[kb_id], documents=[article], metadatas=[{'user': uid}])

    KBCollection.persist()
    # save_file('db_logs/log_%s_update.txt' % time(), 'Updated document %s:%s' % (kb_id, article))
    # TODO - save more info in DB logs, probably as YAML file (original article, new info, final article)

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
        save_file('db_logs/log_%s_split.txt' % time(),
                  'Split document %s, added %s:%s\n%s' % (kb_id, new_id, a1, a2))