from flask import request, jsonify, Blueprint

from chatbot.runner import process_user_message

message_bp = Blueprint('message', __name__)


@message_bp.route('', methods=['POST'])
def user_message():
    uid = request.json.get('uid')
    cid = request.json.get('cid')
    prompt = request.json.get('prompt')
    conversation = request.json.get('conversation')

    # Expecting the following to be text
    response = process_user_message(uid, cid, prompt, conversation)
    return {'response': response}
