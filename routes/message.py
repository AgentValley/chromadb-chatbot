from flask import request, Blueprint

from chatbot.runner import process_user_message
from tools.chat_openai import print_conversation

message_bp = Blueprint('message', __name__)


@message_bp.route('', methods=['POST'])
def user_message():
    uid = request.json.get('uid')
    cid = request.json.get('cid')
    prompt = request.json.get('prompt')
    conversation = request.json.get('conversation')

    # Log messages to monitoring
    print_conversation(uid, cid, conversation, prompt)

    # Expecting the following to be text
    response = process_user_message(uid, cid, prompt, conversation)
    return {'response': response}
