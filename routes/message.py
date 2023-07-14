from flask import request, jsonify, Blueprint

from chatbot.runner import process_user_message

message_bp = Blueprint('message', __name__)


@message_bp.route('', methods=['POST'])
def user_message():
    uid = request.json.get('uid')
    cid = request.json.get('cid')
    message = request.json.get('message')
    chat_history = request.json.get('chat_history')

    # Expecting the following to be text
    response = process_user_message(uid, cid, message, chat_history)
    return response
