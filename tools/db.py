import chromadb
import os

from chromadb.config import Settings

from logger import log_error


class ChromaDBClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = cls.initialize_chromadb()
        return cls._instance

    @staticmethod
    def initialize_chromadb():
        persist_directory = os.getenv("PERSIST_DIR", "../_chromadb_")
        chroma_client = chromadb.Client(
            Settings(persist_directory=persist_directory,
                     chroma_db_impl="duckdb+parquet"))
        return chroma_client

    @staticmethod
    def persist():
        try:
            ChromaDBClient._instance.persist()
        except Exception as e:
            log_error(f'Failed to persist ChromaDB using client{e}')

