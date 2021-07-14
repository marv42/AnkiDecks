#!/usr/bin/env python3
import logging
import re
from logging import DEBUG

import requests
from bs4 import BeautifulSoup

from AnkiServer import *

DECK_NAME_HUNDE = "Hunderassen"
WIKIPEDIA_URL = "https://de.wikipedia.org"
DOGS_URL = f"{WIKIPEDIA_URL}/wiki/Hunderasse"
UPLOAD_COMMONS = "//upload\\.wikimedia\\.org/wikipedia/commons"
DOG_NAME_COLUMN = 2


def scrape_wikipedia():
    dog_info = {}
    result = requests.get(DOGS_URL)
    parsed_html = BeautifulSoup(result.text, 'lxml')
    all_trs = parsed_html.find_all("tr")
    for tr in all_trs:
        if 'Position' in str(tr) or "Gesamtzahl" in str(tr):
            continue
        info = tr.text.split('\n')
        dog = info[DOG_NAME_COLUMN]
        match = re.search(r" href=\"(.+?)\"", str(tr))
        dog_name_url = f"{WIKIPEDIA_URL}{match.group(1)}"
        dog_pic_url = get_dog_pic_url(dog_name_url)
        dog_info[dog] = [dog_pic_url]
    return dog_info


def get_dog_pic_url(dog_name_url):
    result = requests.get(dog_name_url)
    match = re.search(fr"({UPLOAD_COMMONS}.+?\.jpg)\"", result.text)
    dog_pic_url = f"https:{match.group(1)}"
    logging.debug(dog_pic_url)
    return dog_pic_url


def get_dog_note(dog, picture_url):
    return get_card(DECK_NAME_HUNDE, "Hunderasse: ?", dog, picture_url)


logging.basicConfig(level=DEBUG)
invoke('createDeck', deck=DECK_NAME_HUNDE)
dog_info = scrape_wikipedia()
for dog in dog_info:
    dog_note = get_dog_note(dog, dog_info[dog])
    json_add_notes = [dog_note]
    invoke('addNotes', notes=json_add_notes)
