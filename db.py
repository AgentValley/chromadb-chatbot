import chromadb
from chromadb.config import Settings


class ChromaDBClient:
    def __init__(self, persist_directory):
        self.persist_directory = persist_directory
        self.chroma_client = self.initialize_chromadb()

    def initialize_chromadb(self):
        chroma_client = chromadb.Client(
            Settings(persist_directory=self.persist_directory, chroma_db_impl="duckdb+parquet"))
        return chroma_client

    # Implement ChromaDB operations and interactions here
