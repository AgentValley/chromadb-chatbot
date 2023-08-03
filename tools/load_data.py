import os
import re
from multiprocessing import Process
from time import sleep
from uuid import uuid4

import openai
from dotenv import load_dotenv
from llama_index import download_loader, TrafilaturaWebReader

from logger import log_info
from tools import KBCollection
from tools.chat_openai import chat_with_open_ai
from tools.text_cleaner import clean_text

load_dotenv()
MAX_TOKENS = 4000
openai.api_key = os.getenv('OPENAI_API_KEY')


def extract_urls_from_message(message):
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = re.findall(url_pattern, message)
    return urls


def extract_youtube_links(urls):
    youtube_pattern = re.compile(
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)([a-zA-Z0-9\-_]+)')
    youtube_links = [url for url in urls if re.match(youtube_pattern, url)]
    return youtube_links


def load_qna_from_documents(uid, documents):
    document_texts = [clean_text(document.__str__()) for document in documents]

    qnadocuments = []
    for document in document_texts:
        response = chat_with_open_ai(conversation=[{'role': 'system', 'content': document},
                                                   {'role': 'user',
                                                    'content': 'create a list of faqs along with answers on the topics and '
                                                               'concepts from the above text.'}])
        chunks = response.split('\n\n')
        qnadocuments.extend(chunks)

    log_info(f'Embedding text', qnadocuments)
    collection = KBCollection(uid=uid)
    collection.add(
        ids=[str(uuid4()) for x in range(0, len(qnadocuments))],
        documents=qnadocuments,
        metadatas=[{'user': uid} for x in range(0, len(qnadocuments))]
    )
    KBCollection.persist()


def load_web_data_from_urls(uid, urls):
    documents = TrafilaturaWebReader().load_data(urls)
    document_texts = [document.__str__() for document in documents]

    load_qna_from_documents(uid, document_texts)
    log_info(f'Finished loading data from urls {urls}')


def load_transcript_data_from_youtube(uid, urls):
    YoutubeTranscriptReader = download_loader("YoutubeTranscriptReader")
    loader = YoutubeTranscriptReader()
    documents = loader.load_data(ytlinks=urls)
    document_texts = [document.__str__() for document in documents]
    log_info(f'Load URLs from {urls}, got {document_texts} chars')

    collection = KBCollection()
    collection.add(
        ids=[str(uuid4()) for x in range(0, len(document_texts))],
        documents=document_texts,
        metadatas=[{'user': uid}]
    )
    KBCollection.persist()
    log_info(f'Finished loading data from urls {urls}')


def load_data_from_urls(uid, message):

    # Extract web urls and youtube links
    urls = extract_urls_from_message(message)
    if urls:
        load_web_data = Process(target=load_web_data_from_urls, args=[uid, urls, ])
        load_web_data.start()

    youtube_urls = extract_youtube_links(urls)
    if youtube_urls:
        load_transcript = Process(target=load_transcript_data_from_youtube, args=[uid, youtube_urls, ])
        load_transcript.start()

    return urls or youtube_urls


def load_data_from_pdf(uid, file):
    log_info("load_data_from_pdf UID", uid)
    log_info("load_data_from_pdf File Data", file)
