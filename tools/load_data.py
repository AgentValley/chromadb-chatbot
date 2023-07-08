import os
import re
from multiprocessing import Process
from time import sleep
from uuid import uuid4

import openai
from dotenv import load_dotenv
from llama_index import download_loader, TrafilaturaWebReader

# from utils import save_yaml

load_dotenv()

MAX_TOKENS = 4000

# instantiate chatbot
openai.api_key = os.getenv('OPENAI_API_KEY')

# conversation = list()


from tools import KBCollection


def chat_with_open_ai(conversation, model="gpt-3.5-turbo-16k", temperature=0):
    max_retry = 3
    retry = 0
    messages = [{'role': x.get('role', 'assistant'),
                 'content': x.get('content', '')} for x in conversation]
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
            text = response['choices'][0]['message']['content']

            # trim message object
            debug_object = [i['content'] for i in messages]
            debug_object.append(text)
            # save_yaml('api_logs/convo_%s.yaml' % time(), debug_object)
            if response['usage']['total_tokens'] >= MAX_TOKENS:
                messages = split_long_messages(messages)
                if len(messages) > 1:
                    messages.pop(1)

            return text
        except Exception as oops:
            print(f'Error communicating with OpenAI: "{oops}"')
            if 'maximum context length' in str(oops):
                messages = split_long_messages(messages)
                if len(messages) > 1:
                    messages.pop(1)
                print(' DEBUG: Trimming oldest message')
                continue
            retry += 1
            if retry >= max_retry:
                print(f"Exiting due to excessive errors in API: {oops}")
                return str(oops)
            print(f'Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)


def split_long_messages(messages):
    new_messages = []
    for message in messages:
        content = message['content']
        if len(content.split()) > 1000:
            # Split the content into chunks of 4096 tokens
            chunks = [content[i:i + 1000] for i in range(0, len(content), 1000)]

            # Create new messages for each chunk
            for i, chunk in enumerate(chunks):
                new_message = {'role': message['role'], 'content': chunk}
                if i == 0:
                    # Replace the original message with the first chunk
                    new_messages.append(new_message)
                else:
                    # Append subsequent chunks as new messages
                    new_messages.append({'role': message['role'], 'content': chunk})
        else:
            new_messages.append(message)  # No splitting required, add original message as it is

    return new_messages


def extract_urls_from_message(message):
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = re.findall(url_pattern, message)
    return urls


def extract_youtube_links(urls):
    youtube_pattern = re.compile(
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)([a-zA-Z0-9\-_]+)')
    youtube_links = [url for url in urls if re.match(youtube_pattern, url)]
    return youtube_links


def clean_text(text):
    # Remove extra spaces and newlines
    cleaned_text = re.sub('\s+', ' ', text).strip()

    # Remove all newline characters
    cleaned_text = cleaned_text.replace('\n', '')

    return cleaned_text


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

    print(f'Embedding text', qnadocuments)
    collection = KBCollection(uid=uid)
    collection.add(
        ids=[str(uuid4()) for x in range(0, len(qnadocuments))],
        documents=qnadocuments,
        metadatas=[{'user': uid} for x in range(0, len(qnadocuments))]
    )
    KBCollection.persist()


def load_web_data_from_urls(uid, urls):
    # documents = TrafilaturaWebReader().load_data(urls)

    # loader = download_loader("BeautifulSoupWebReader")()
    # documents = loader.load_data(urls=urls)
    #
    # # index = GPTVectorStoreIndex.from_documents(documents)
    # # print(index.query('What language is on this website?'))
    #
    # document_texts = [document.__str__() for document in documents]
    # print(f'Load URLs from {urls}, got {len(document_texts)} chars')

    documents = TrafilaturaWebReader().load_data(urls)
    load_qna_from_documents(uid, documents)
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
    KBCollection.persist()
    print(f'Finished loading data from urls {urls}')


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


def load_data_from_pdf(uid, file):
    print("UID", uid)
    print("File Data", file)
