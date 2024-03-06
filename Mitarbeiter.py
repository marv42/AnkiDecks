#!/usr/bin/env python3
import os
from glob import glob
from logging import DEBUG

from AnkiServer import *

DECK_NAME_NAMES = 'Mitarbeiter: Namen'
DECK_NAME_IDS = 'Mitarbeiter: Kürzel'
PICTURE_PATH = 'dia'


def get_name_note(pic_path, name, abbreviation):
    absolute_path = f"{os.path.abspath(os.getcwd())}/{pic_path}"
    return get_card(DECK_NAME_NAMES, "Name: ?<br>", f"{name} ({abbreviation})", [absolute_path])


def get_name(pic_path):
    underscore = pic_path.find("_")
    dot = pic_path.find(".")
    return pic_path[underscore + 1 : dot]


def get_abbreviation(pic_path):
    slash = pic_path.find("/")
    underscore = pic_path.find("_")
    return pic_path[slash + 1 : underscore]


logging.basicConfig(level=DEBUG)
invoke('createDeck', deck=DECK_NAME_NAMES)
pics = glob(f"{PICTURE_PATH}/*.jpg")
for pic_path in pics:
    name = get_name(pic_path)
    abbreviation = get_abbreviation(pic_path)
    pic_note = get_name_note(pic_path, name, abbreviation)
    logging.debug(f"adding {pic_note}")
    invoke('addNote', note=pic_note)
