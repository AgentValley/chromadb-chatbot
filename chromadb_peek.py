import os
import chromadb
from chromadb.config import Settings
from pprint import pprint as pp

from dotenv import load_dotenv

load_dotenv()

persist_directory = os.getenv("PERSIST_DIR", "_chromadb_")

chroma_client = chromadb.Client(Settings(persist_directory=persist_directory,chroma_db_impl="duckdb+parquet",))
collection = chroma_client.get_or_create_collection(name="knowledge_base")


print('KB presently has %s entries' % collection.count())
print('\n\nBelow are the top 10 entries:')
results = collection.peek()
# pp(results)