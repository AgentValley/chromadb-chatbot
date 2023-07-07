import os

from flask import Flask, jsonify
from dotenv import load_dotenv

from routes.message import message_bp
from routes.upload import upload_bp

load_dotenv()

app = Flask(__name__)

upload_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


@app.route('/', methods=['GET'])
def hello():
    return jsonify('AV ChromaDB')


app.register_blueprint(message_bp, url_prefix='/message')
app.register_blueprint(upload_bp, url_prefix='/upload')


if __name__ == '__main__':
    app.run(port=5010, load_dotenv=True)
