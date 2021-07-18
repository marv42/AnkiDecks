#!/usr/bin/env python3
import logging
from logging import DEBUG

import requests
from bs4 import BeautifulSoup

from AnkiServer import *

DECK_NAME_BAEUME = 'Bäume'
BAUMKUNDE = 'https://www.baumkunde.de/'
TREES_URL = f'{BAUMKUNDE}haeufigste-baeume-deutschland.php'


def scrape_site():
    tree_2_info = {}
    result = requests.get(TREES_URL)
    soup = BeautifulSoup(result.text, 'lxml')
    all_divs = soup.find_all(attrs={"class": "card mb-3"})
    for div in all_divs:
        name = div.h2.text
        tree_links = get_tree_links(div)
        if tree_links not in name:
            name += f"<br>({tree_links})"
        tree_pic_url = get_pic_url(div, 'imgHabitus')
        leave_pic_url = get_pic_url(div, 'imgBlatt')
        tree_2_info[name] = [tree_pic_url, leave_pic_url]
    return tree_2_info


def get_tree_links(div):
    for descendant in div.descendants:
        if class_is_name(descendant, 'baumLinks'):
            tree_links = []
            for tree_link in descendant.text.split('\n'):
                if tree_link:
                    tree_links.append(tree_link.strip())
            if len(tree_links) > 0:
                return ', '.join(tree_links)
    return ""


def get_pic_url(div, class_name):
    for descendant in div.descendants:
        if class_is_name(descendant, class_name):
            return f"{BAUMKUNDE}{descendant.img['src']}"


def class_is_name(descendant, class_name):
    return descendant.name == 'div' and \
           'class' in descendant.attrs.keys() and \
           class_name in descendant['class'][0]


def get_tree_note(tree_info, pictures):
    return get_card(DECK_NAME_BAEUME, "Baum/Strauch: ?<br>", tree_info, pictures)


logging.basicConfig(level=DEBUG)
invoke('createDeck', deck=DECK_NAME_BAEUME)
tree_2_info = scrape_site()
for tree_info in tree_2_info:
    pictures = tree_2_info[tree_info]
    tree_note = get_tree_note(tree_info, pictures)
    logging.debug(f"adding {tree_info}")
    invoke('addNote', note=tree_note)
