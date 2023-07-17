import os
from dotenv import load_dotenv

load_dotenv()

# File System
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
CONVERSATION_DIR = os.path.join(os.path.dirname(__file__), 'conversations')

SPACY_DATA = os.path.join(os.path.dirname(__file__), 'spacy_data')

# Internal
ENV = os.getenv('ENV', 'dev')
SHARED_SECRET_KEY = os.getenv('SHARED_SECRET_KEY', 'my_precious')

GRAPHDB_ENDPOINT = os.getenv('GRAPHDB_ENDPOINT')


# Logging
SERVER_LOG_FILE = os.getenv('SERVER_LOG_FILE')
WORKER_LOG_FILE = os.getenv('WORKER_LOG_FILE')
NEWRELIC_INI_FILE = os.getenv('NEWRELIC_INI_FILE')

# 3rd Party
TELEGRAM_BOT_URL = os.getenv('TELEGRAM_BOT_URL')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', 4000))
OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', 0.9))
OPENAI_STOP_SEQ = os.getenv('OPENAI_STOP_SEQ', '\n')