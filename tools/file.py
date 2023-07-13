import os
import yaml


def open_file(filepath):
    with open(os.getcwd() + '/' + filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()


def save_yaml(filepath, data):
    with open(os.getcwd() + '/' + filepath, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True)


def save_file(filepath, content):
    with open(os.getcwd() + '/' + filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)
