import requests
import urllib.request
from abc import ABC
from html.parser import HTMLParser


class MyHTMLParser(HTMLParser, ABC):
    pic_url = None
    in_h3 = False

    @staticmethod
    def fix_encoding(string):
        return string.encode('latin1').decode('unicode_escape').encode('latin1').decode()

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            for attr in attrs:
                if attr[0] == 'src':
                    self.pic_url = self.fix_encoding(attr[1])
        if tag == 'h3':
            self.in_h3 = True

    def handle_endtag(self, tag):
        if tag == 'h3':
            self.in_h3 = False

    def handle_data(self, data):
        if self.in_h3:
            self.save_pic(self.pic_url, self.fix_encoding(data))

    @staticmethod
    def save_pic(url, name):
        img_data = requests.get(url).content
        with open(f'cards/{name}.jpg', 'wb') as handler:
            handler.write(img_data)


alle_rassen = str(urllib.request.urlopen('https://www.hundeo.com/hunderassen/').read())

parser = MyHTMLParser()
parser.feed(alle_rassen)
