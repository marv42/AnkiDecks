#!/usr/bin/env python3
import logging
import os
from glob import glob
from logging import DEBUG

from AnkiServer import *

DECK_NAME_NAMES = 'Mitarbeiter: Namen'
DECK_NAME_IDS = 'Mitarbeiter: Kürzel'
PICTURE_PATH = 'dia'


def get_name_note(pic_path, name):
    absolute_path = f"{os.path.abspath(os.getcwd())}/{pic_path}"
    return get_card(DECK_NAME_NAMES, "Name: ?<br>", name, [absolute_path])


def get_name(pic_path):
    underscore = pic_path.find("_")
    dot = pic_path.find(".")
    return pic_path[underscore + 1 : dot]


logging.basicConfig(level=DEBUG)
invoke('createDeck', deck=DECK_NAME_NAMES)
pics = glob(f"{PICTURE_PATH}/*.jpg")
for pic_path in pics:
    name = get_name(pic_path)
    pic_note = get_name_note(pic_path, name)
    logging.debug(f"adding {pic_note}")
    invoke('addNote', note=pic_note)
