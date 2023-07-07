import chromadb
import openai
from chromadb import Settings

# instantiate ChromaDB
persist_directory = "_chromadb_"
chroma_client = chromadb.Client(Settings(persist_directory=persist_directory, chroma_db_impl="duckdb+parquet", ))


class KBCollection:
    _collection = None

    @staticmethod
    def __new__(cls, name="knowledge_base"):
        if not cls._collection:
            cls._collection = chroma_client.get_or_create_collection(name=name)
        return cls._collection

