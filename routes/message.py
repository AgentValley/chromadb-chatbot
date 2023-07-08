from flask import request, jsonify, Blueprint

from tools.chatbot import process_user_message

message_bp = Blueprint('message', __name__)


@message_bp.route('/', methods=['POST'])
def user_message():
    uid = request.json.get('uid')
    cid = request.json.get('cid')
    message = request.json.get('message')
    chat_history = request.json.get('chat_history')
    response = process_user_message(uid, cid, message, chat_history)
    return jsonify({'response': response})
