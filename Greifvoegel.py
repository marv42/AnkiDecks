#!/usr/bin/env python3
from logging import DEBUG
import requests
from AnkiServer import *

DECK_NAME_BIRDS = "Greifvögel"
BIRDS_URL = "https://www.gartenlexikon.de/heimische-greifvoegel/"


def scrape_wikipedia():
    birds_info = {}
    result = requests.get(BIRDS_URL)
    soup = BeautifulSoup(result.text, 'lxml')
    all_strongs = soup.find_all("strong")
    for strong in all_strongs:
        if "class" in str(strong) or "Gartenkalender" in str(strong):
            continue
        name = strong.text
        picture_url = get_picture_url(soup, strong)
        birds_info[name] = picture_url
    return birds_info


def get_picture_url(soup, strong):
    search_name = strong.text.split(" ")[0]
    all_imgs = soup.find_all("img")
    for img in all_imgs:
        if search_name in img["alt"]:
            if "data-lazy-src" in str(img):
                img_src = img["data-lazy-src"]
                if "erkennen" in img_src:
                    continue
                return img_src
            img_src = img["src"]
            if "erkennen" in img_src:
                continue
            return img_src
    raise Exception("No URL found")


logging.basicConfig(level=DEBUG)
invoke('createDeck', deck=DECK_NAME_BIRDS)
birds_info = scrape_wikipedia()
logging.debug(f"len: {len(birds_info)}")


def get_bird_note(name, url):
    return get_card(DECK_NAME_BIRDS, "Greifvogel: ?<br>", name, [url])


for info in birds_info:
    bird_note = get_bird_note(info, birds_info[info])
    logging.debug(f"adding {bird_note}")
    invoke('addNote', note=bird_note)
