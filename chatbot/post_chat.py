from chatbot.kb import first_KB, update_KB
from chatbot.profile import update_user_profile
from tools import KBCollection
from tools.text_cleaner import generate_scratchpad


def post_processing(uid, current_user_profile, conversation):
    print(f'Starting post processing...')

    user_messages = [x for x in conversation if x.get('role') == 'user']
    user_scratchpad = generate_scratchpad(user_messages, user=True)

    # update user profile
    update_user_profile(uid, current_user_profile, user_scratchpad)
    main_scratchpad = generate_scratchpad(conversation)

    # Update the knowledge base
    collection = KBCollection(uid=uid)
    if collection.count() == 0:
        print('Create first KB...')
        first_KB(uid, main_scratchpad)
    else:
        print('Updating KB...')
        update_KB(uid, main_scratchpad)

    KBCollection.persist()
    print(f'Finished post processing...')
