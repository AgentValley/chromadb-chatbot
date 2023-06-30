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
    content = request.json.get('message')
    user_id = request.json.get('user_id')
    response = process_user_message(user_id, content)
    return jsonify({'response': response})


if __name__ == '__main__':
    app.run(port=5010, load_dotenv=True)
