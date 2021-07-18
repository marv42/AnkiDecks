#!/usr/bin/env python3
import logging
from logging import DEBUG
import re

import requests
from bs4 import BeautifulSoup

from AnkiServer import *

DECK_NAME_COUNTRIES = 'Geographie: Staaten'
DECK_NAME_CAPITALS = 'Geographie: Hauptstädte'
WIKIPEDIA_URL = "https://de.wikipedia.org"
UPLOAD_COMMONS = "//upload\\.wikimedia\\.org/wikipedia/commons"
COUNTRIES_URL = f"{WIKIPEDIA_URL}/wiki/Liste_der_Staaten_der_Erde"
COLUMN_STATE = 1
COLUMN_LONG_NAME = 3
COLUMN_CAPITAL = 5
COLUMN_ISO = 17
COLUMN_TLD = 21


def get_country_note(country_info, pictures):
    return get_card(DECK_NAME_COUNTRIES, "Staat oder Gebiet: ?<br>", country_info, pictures)


def get_capital_note(country_info, capital, pictures):
    return get_card(DECK_NAME_CAPITALS, f"{country_info}<br>Hauptstadt: ?<br>", capital, pictures)


def scrape_wikipedia():
    country_2_info = {}
    result = requests.get(COUNTRIES_URL)
    parsed_html = BeautifulSoup(result.text, 'lxml')
    all_trs = parsed_html.find_all("tr")
    for tr in all_trs:
        if 'hintergrundfarbe' in str(tr):
            continue
        info = tr.text.split('\n')
        state_name = get_state_name(tr)
        name = f"{state_name}<br>" \
               f"Langform: {remove_references_and_hyphen(info[COLUMN_LONG_NAME])}"
        if len(info) >= COLUMN_ISO and info[COLUMN_ISO]:
            name += f"<br>ISO-3: {info[COLUMN_ISO]}"
        if len(info) >= COLUMN_TLD and info[COLUMN_TLD]:
            name += f"<br>TLD: {info[COLUMN_TLD]}"
        location_url = get_location_url(tr)
        flag_url = get_flag_url(tr)
        capital = remove_references_and_hyphen(info[COLUMN_CAPITAL])
        country_2_info[name] = [capital, [location_url, flag_url]]
    return country_2_info


def get_state_name(tr):
    parsed = BeautifulSoup(str(tr), 'lxml')
    a_href = parsed.find("a")
    state_name = a_href.text
    logging.debug(state_name)
    return state_name


def remove_references_and_hyphen(s):
    s = re.sub(r"\[.*?\]", "", s)
    return re.sub("\\xad", "", s)


def get_flag_url(tr):
    match = re.search(r"/wiki/Datei:Flag_of_.+?\.svg", str(tr))
    if match:
        flag_site_url = f"{WIKIPEDIA_URL}{match.group(0)}"
        logging.debug(flag_site_url)
        return get_flag_url_from_flag_site(flag_site_url)
    match = re.search(r"(/wiki/.+?)\"", str(tr))
    if match:
        flag_site_url = f"{WIKIPEDIA_URL}{match.group(1)}"
        logging.debug(flag_site_url)
        return get_flag_url_from_flag_site(flag_site_url)
    raise Exception("No flag url found")


def get_flag_url_from_flag_site(flag_site_url):
    result = requests.get(flag_site_url)
    match = re.search(fr"{UPLOAD_COMMONS}.+?Flag_of_.+?\.png", result.text)
    flag_url = match.group(0)
    logging.debug(flag_url)
    return f"https:{flag_url}"


def get_location_url(tr):
    result = request_wiki_data_site(tr)
    result = request_map_site(result.text)
    return get_map_url(result.text)


def request_wiki_data_site(tr):
    wiki_data_url = get_wiki_data_url(tr)
    return requests.get(wiki_data_url)


def get_wiki_data_url(tr):
    parsed_tr = BeautifulSoup(str(tr), 'lxml')
    wiki_link = parsed_tr.find("a")  # , href=True
    result = requests.get(f"{WIKIPEDIA_URL}{wiki_link['href']}")
    state_site = result.text
    match = re.search(r"(https://www\.wikidata\.org/wiki/Special:EntityPage/Q.+?)#sitelinks-wikipedia", state_site)
    if not match:
        raise Exception(f"No wikidata site on state site {state_site}")
    wiki_data_url = match.group(1)
    logging.debug(wiki_data_url)
    return wiki_data_url


def request_map_site(wiki_data_site):
    map_site_url = get_map_site_url(wiki_data_site)
    return requests.get(map_site_url)


def get_map_site_url(wiki_data_site):
    for part_of_picture_url in ["orthographic", "ocation", "Locator_map_of_", "_Current_en", "_in_its_region",
                                 "_on_the_globe_", "-"]:
        match = re.search(fr"(https://commons\.wikimedia\.org/wiki/File:.*?{part_of_picture_url}.*?\.(svg|png))\"",
                          wiki_data_site)
        if match:
            map_site_url = match.group(1)
            logging.debug(map_site_url)
            return map_site_url
    raise Exception(f"No map site with part_of_picture_url on wikidata site found")


def get_map_url(map_site):
    match = re.search(fr"(https:{UPLOAD_COMMONS}.+?\.png)\"", map_site)
    if not match:
        raise Exception(f"No picture with pattern on map site")
    map_url = match.group(1)
    logging.debug(map_url)
    return map_url


logging.basicConfig(level=DEBUG)
invoke('createDeck', deck=DECK_NAME_COUNTRIES)
invoke('createDeck', deck=DECK_NAME_CAPITALS)
country_2_info = scrape_wikipedia()
for country_info in country_2_info:
    capital = country_2_info[country_info][0]
    pictures = country_2_info[country_info][1]
    country_note = get_country_note(country_info, pictures)
    capital_note = get_capital_note(country_info, capital, pictures)
    json_add_notes = [country_note, capital_note]
    logging.debug(f"adding {country_info}")
    invoke('addNotes', notes=json_add_notes)
