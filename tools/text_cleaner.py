import re

SCRATCHPAD_LENGTH = 5


def clean_text(text):
    # Remove extra spaces and newlines
    cleaned_text = re.sub('\s+', ' ', text).strip()

    # Remove all newline characters
    cleaned_text = cleaned_text.replace('\n', '')

    return cleaned_text


def generate_scratchpad(conversation, user=False, assistant=False):
    if not conversation or len(conversation) < 2:
        return ""

    filtered = []
    for x in conversation[1:]:
        if user and x.get('role') == 'user':
            filtered.append(x)
        elif assistant and x.get('role') == 'assistant':
            filtered.append(x)
        else:
            filtered.append(x)
    scratchpad = '\n'.join([x.get('role', '') + ': ' + x.get('content', '') for x in filtered]).strip()

    return scratchpad

