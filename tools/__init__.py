import chromadb

# instantiate ChromaDB
persist_directory = "_chromadb_"
chroma_client = chromadb.Client(chromadb.Settings(
    persist_directory=persist_directory,
    chroma_db_impl="duckdb+parquet",
))


class KBCollection:
    _collection = None

    @staticmethod
    def __new__(cls, name="knowledge_base", uid=None):
        if not cls._collection:
            if uid:
                cls._collection = chroma_client.get_or_create_collection(name=name, metadata={"user": uid})
        return cls._collection

    @staticmethod
    def persist():
        chroma_client.persist()
