#!/usr/bin/env python3
import logging
from logging import DEBUG
import requests
from AnkiServer import *

DECK_NAME_PAINTINGS = "Most Expensive Paintings"
HTTPS = "https:"
WIKIPEDIA_URL = f"{HTTPS}//en.wikipedia.org"
PAINTINGS_URL = f"{WIKIPEDIA_URL}/wiki/List_of_most_expensive_paintings"
UPLOAD_WIKIMEDIA = "//upload.wikimedia.org/wikipedia/"
COLUMN_PRICE = 0
COLUMN_NAME = 1
COLUMN_ARTIST = 3
COLUMN_IMAGE = 2


def scrape_wikipedia():
    painting_info = []
    result = requests.get(PAINTINGS_URL)
    soup = BeautifulSoup(result.text, 'lxml')
    all_trs = soup.find_all("tr")
    for tr in all_trs:
        tr = str(tr)
        if "Adjusted price" in tr:
            continue
        info = tr.split('</td>')
        if len(info) < 3:
            continue
        pic_url = get_pic_url(info)
        if not pic_url:
            continue
        painting_name = get_text(info[COLUMN_NAME])
        artist = get_text(info[COLUMN_ARTIST])
        price = get_price(info[COLUMN_PRICE])
        painting_info.append([painting_name, artist, price, pic_url])
    return painting_info


def get_pic_url(info):
    image_info = info[COLUMN_IMAGE]
    soup = BeautifulSoup(image_info, 'lxml')
    if soup.a:
        url = request_and_get_upload_jpg(f"{WIKIPEDIA_URL}{soup.a['href']}")
        if url:
            return url
    name_info = info[COLUMN_NAME]
    soup = BeautifulSoup(name_info, 'lxml')
    if soup.a:
        url = f"{soup.a['href']}"
        if "de.wikipedia.org" in url:
            return
        painting_url = prepend_x_if_not_there(url, WIKIPEDIA_URL)
        url = request_and_get_upload_jpg(painting_url)
        if url:
            return url


def request_and_get_upload_jpg(url):
    result = requests.get(url)
    soup = BeautifulSoup(result.text, 'lxml')
    class_list = ["fullImageLink", "infobox-image", "mw-mmv-image", "thumb tright", "mw-parser-output"]
    for c in class_list:
        class_found = soup.find(attrs={"class": c})
        if class_found:
            content = class_found.a.contents[0]
            if 'String' not in str(type(content)):
                src = content['src']
                logging.debug(src)
                return prepend_x_if_not_there(src, HTTPS)


def prepend_x_if_not_there(url, x):
    if not url.startswith(x):
        return f"{x}{url}"
    return url


def get_price(info):
    soup = BeautifulSoup(info, 'lxml')
    return remove_references_and_hyphen(soup.th.text)


def get_painting_note(info):
    name, artist, price, url = info
    return get_card(DECK_NAME_PAINTINGS, "Artist: ?<br>", f"{artist}<br>Painting: {name}<br>Price: {price} m", [url])


logging.basicConfig(level=DEBUG)
invoke('createDeck', deck=DECK_NAME_PAINTINGS)
painting_info = scrape_wikipedia()
for info in painting_info:
    painting_note = get_painting_note(info)
    logging.debug(f"adding {painting_note}")
    invoke('addNote', note=painting_note)
