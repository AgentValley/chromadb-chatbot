import re
from multiprocessing import Process
from uuid import uuid4

from llama_index import TrafilaturaWebReader, download_loader

from tools import KBCollection


def extract_urls_from_message(message):
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = re.findall(url_pattern, message)
    return urls


def extract_youtube_links(urls):
    youtube_pattern = re.compile(
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)([a-zA-Z0-9\-_]+)')
    youtube_links = [url for url in urls if re.match(youtube_pattern, url)]
    return youtube_links


def load_web_data_from_urls(uid, urls):

    documents = TrafilaturaWebReader().load_data(urls)
    document_texts = [document.__str__() for document in documents]
    print(f'Load URLs from {urls}, got {len(document_texts)} chars')

    ids = [str(uuid4()) for x in range(0, len(document_texts))]
    collection = KBCollection()
    collection.add(
        ids=ids,
        documents=document_texts,
        metadatas=[{'user': uid}]
    )
    print(f'Finished loading data from urls {urls}')


def load_transcript_data_from_youtube(uid, urls):
    YoutubeTranscriptReader = download_loader("YoutubeTranscriptReader")
    loader = YoutubeTranscriptReader()
    documents = loader.load_data(ytlinks=urls)
    document_texts = [document.__str__() for document in documents]
    print(f'Load URLs from {urls}, got {document_texts} chars')

    collection = KBCollection()
    collection.add(
        ids=[str(uuid4()) for x in range(0, len(document_texts))],
        documents=document_texts,
        metadatas=[{'user': uid}]
    )
    print(f'Finished loading data from urls {urls}')


def load_data_from_urls(uid, message):

    # Extract web urls and youtube links
    urls = extract_urls_from_message(message)
    if urls:
        load_web_data = Process(target=load_web_data_from_urls, args=[uid, urls, ])
        load_web_data.start()

    youtube_urls = extract_youtube_links(urls)
    if youtube_urls:
        load_transcript = Process(target=load_transcript_data_from_youtube, args=[uid, youtube_urls, collection, ])
        load_transcript.start()


def load_data_from_pdf(uid, file):
    print("UID", uid)
    print("File Data", file)

