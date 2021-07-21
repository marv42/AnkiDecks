#!/usr/bin/env python3
import json
import logging
import re
import urllib.request
from bs4 import BeautifulSoup

ANKI_SERVER = 'http://localhost:8765'


def get_request(action, **params):
    return {'action': action, 'params': params, 'version': 6}


def invoke(action, **params):  # cf. https://github.com/FooSoft/anki-connect
    request_data = get_request(action, **params)
    request_json = json.dumps(request_data).encode('utf-8')
    request_url = urllib.request.Request(ANKI_SERVER, request_json)
    http_response = urllib.request.urlopen(request_url)
    response = json.load(http_response)
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def get_card(deck_name, front, back, pictures):
    return {
        "deckName": deck_name,
        "modelName": "Basic",
        "fields": {
            "Front": front,
            "Back": back
        },
        "options": get_options(deck_name),
        "picture": get_picture(pictures)
    }


def get_options(deck_name):
    return {
        "allowDuplicate": False,
        "duplicateScope": "deck",
        "duplicateScopeOptions": {
            "deckName": deck_name,
            "checkChildren": False
        }
    }


def get_picture(pictures):
    picture_list = []
    for picture_url in pictures:
        file_name = get_file_name(picture_url, '/')  # TODO ':'?
        picture = {
            "url": picture_url,
            "filename": file_name,
            "fields": [
                "Front"
            ]
        }
        picture_list.append(picture)
    return picture_list


def get_file_name(url, last_symbol_not_in_name):
    return url[url.rfind(last_symbol_not_in_name) + 1:]


def get_text(info):
    info = info.replace("<br>", " ").replace("<br/>", " ")
    soup = BeautifulSoup(info, 'lxml')
    text = remove_references_and_hyphen(soup.text)
    logging.debug(text)
    return text


def remove_references_and_hyphen(s):
    s = re.sub(r"\[.*?\]", "", s)
    s = re.sub("\\xad", "", s)
    return re.sub("\\n", "", s)
