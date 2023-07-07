import os
import re
import yaml


def open_file(filepath):
    with open(os.getcwd() + '/' + filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()


def save_yaml(filepath, data):
    with open(os.getcwd() + '/' + filepath, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True)


def save_file(filepath, content):
    with open(os.getcwd() + '/' + filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


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