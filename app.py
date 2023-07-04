from flask import Flask, request, jsonify
from chatbot import process_user_message
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


@app.route('/', methods=['GET'])
def hello():
    return jsonify('AV ChromaDB')


@app.route('/message', methods=['POST'])
def user_message():
    uid = request.json.get('uid')
    course_name = request.json.get('course_name')
    message = request.json.get('message')
    chat_history = request.json.get('chat_history')
    response = process_user_message(uid, course_name, message, chat_history)
    return jsonify({'response': response})


if __name__ == '__main__':
    app.run(port=5010, load_dotenv=True)
