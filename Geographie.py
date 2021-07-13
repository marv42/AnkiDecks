#!/usr/bin/env python3
import json
import logging
from logging import DEBUG
import re
import urllib.request

import requests
from bs4 import BeautifulSoup

ANKI_SERVER = 'http://localhost:8765'
DECK_NAME_COUNTRIES = 'Geographie: Staaten'
DECK_NAME_CAPITALS = 'Geographie: Hauptstädte'
WIKIPEDIA_URL = "https://de.wikipedia.org"
COUNTRIES_URL = f"{WIKIPEDIA_URL}/wiki/Liste_der_Staaten_der_Erde"
COLUMN_STATE = 1
COLUMN_LONG_NAME = 3
COLUMN_CAPITAL = 5
COLUMN_ISO = 17
COLUMN_TLD = 21


def get_request(action, **params):
    return {'action': action, 'params': params, 'version': 6}


def invoke(action, **params):
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


def get_country_note(country_info, pictures):
    return get_card(DECK_NAME_COUNTRIES, "Staat oder Gebiet: ?", country_info, pictures)


def get_capital_note(country_info, capital, pictures):
    return get_card(DECK_NAME_CAPITALS, f"{country_info}<br>Hauptstadt: ?", capital, pictures)


def get_card(deck_name, front, back, pictures):
    return {
        "deckName": deck_name,
        "modelName": "Basic",
        "fields": {
            "Front": front,
            "Back": back
        },
        "options": get_options(deck_name),
        "picture": get_picture(pictures[0], pictures[1])
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


def get_picture(location_url, flag_url):
    file_name_location = get_file_name(location_url, ':')
    file_name_flag = get_file_name(flag_url, '/')
    return [{
        "url": location_url,
        "filename": file_name_location,
        "fields": [
            "Front"
        ]
    },
    {
        "url": flag_url,
        "filename": file_name_flag,
        "fields": [
            "Front"
        ]
    }]


def get_file_name(url, last_symbol_not_in_name):
    return url[url.rfind(last_symbol_not_in_name) + 1:]


def scrape_wikipedia():
    country_2_info = {}
    result = requests.get(COUNTRIES_URL)
    parsed_html = BeautifulSoup(result.text, 'lxml')
    all_trs = parsed_html.find_all("tr")
    for tr in all_trs:
        if 'hintergrundfarbe' in str(tr):
            continue
        info = tr.text.split('\n')
        name = f"{remove_references_and_hyphen(info[COLUMN_STATE])}<br>" \
               f"Langform: {remove_references_and_hyphen(info[COLUMN_LONG_NAME])}<br>" \
               f"ISO-3: {info[COLUMN_ISO]}"
        if len(info) >= COLUMN_TLD and info[COLUMN_TLD]:
            name += f"<br>TLD: {info[COLUMN_TLD]}"
        location_url = get_location_url(tr)
        flag_url = get_flag_url(tr)
        country_2_info[name] = [info[COLUMN_CAPITAL], [location_url, flag_url]]
    return country_2_info


def remove_references_and_hyphen(s):
    s = re.sub(r"\[.*?\]", "", s)
    return re.sub("\\xad", "", s)


def get_flag_url(tr):
    match = re.search(r" (//upload\.wikimedia\.org.+?px-Flag_of_.+?\.png)", str(tr))
    # TODO /wiki/Datei:Flag_of
    return f"https:{match.group(1)}"


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
    for part_of_picture_url in ["ocation", "Locator_map_of_", "orthographic", "_Current_en", "_in_its_region",
                                 "_on_the_globe_", "-"]:
        match = re.search(fr"(https://commons\.wikimedia\.org/wiki/File:.*?{part_of_picture_url}.*?\.(svg|png))\"",
                          wiki_data_site)
        if match:
            map_site_url = match.group(1)
            logging.debug(map_site_url)
            return map_site_url
    raise Exception(f"No map site with part_of_picture_url on wikidata site found")


def get_map_url(map_site):
    match = re.search(fr"https://upload.wikimedia.org/wikipedia/commons/.+?px-.+?.png", map_site)
    if not match:
        raise Exception(f"No picture with pattern on map site")
    return match.group(0)


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
