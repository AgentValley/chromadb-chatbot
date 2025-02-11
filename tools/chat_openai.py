from time import sleep

import openai

from const import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS, OPENAI_TEMPERATURE
from logger import log_info, log_error, log_warn

openai.api_key = OPENAI_API_KEY


def chat_with_open_ai(conversation, model=OPENAI_MODEL, temperature=OPENAI_TEMPERATURE):
    max_retry = 3
    retry = 0
    messages = [{'role': x.get('role', 'assistant'),
                 'content': x.get('content', '')} for x in conversation]

    while True:
        try:
            # log_info('Calling OPENAI', messages)
            response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
            # log_info('OPENAI Response', response)
            text = response['choices'][0]['message']['content']

            # trim message object
            debug_object = [i['content'] for i in messages]
            debug_object.append(text)
            if response['usage']['total_tokens'] >= OPENAI_MAX_TOKENS:
                messages = split_long_messages(messages)
                if len(messages) > 1:
                    messages.pop(1)

            return text
        except Exception as oops:
            log_warn(f'Error communicating with OpenAI: "{oops}"')
            if 'maximum context length' in str(oops):
                messages = split_long_messages(messages)
                if len(messages) > 1:
                    messages.pop(1)
                log_warn(' DEBUG: Trimming oldest message')
                continue
            retry += 1
            if retry >= max_retry:
                log_warn(f"Exiting due to excessive errors in API: {oops}")
                return str(oops)
            log_warn(f'Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)


def print_conversation(uid, cid, conversation, prompt):
    output = []
    for msg in conversation:
        role = msg.get('role', 'assistant')
        content = msg.get('content', '')

        # Trim long content if needed
        if role != 'system' and len(content) > 300:
            content = f'{content[:180]}...\n...{content[-100:]}'

        role = f'💬 {role}: ' if role == 'user' else f'🤖 {role}: '
        output.append(f'{role} {content}')
    output.append(f'💬 [user] {prompt}')
    log_warn(f'💬 Conversation : UID: {uid} - CID: {cid}\n' + '\n'.join(output))


def print_response(uid, cid, response):
    log_warn(f'🤖 RESPONSE: USER: {uid} - CID: {cid}\n' + f'🤖 [assistant] {response}')


def split_long_messages(messages):
    new_messages = []
    for message in messages:
        content = message['content']
        if len(content.split()) > 1000:
            # Split the content into chunks of 4096 tokens
            chunks = [content[i:i + 1000] for i in range(0, len(content), 1000)]

            # Create new messages for each chunk
            for i, chunk in enumerate(chunks):
                new_message = {'role': message['role'], 'content': chunk}
                if i == 0:
                    # Replace the original message with the first chunk
                    new_messages.append(new_message)
                else:
                    # Append subsequent chunks as new messages
                    new_messages.append({'role': message['role'], 'content': chunk})
        else:
            new_messages.append(message)  # No splitting required, add original message as it is

    return new_messages
