"""Handle control over dolphin parsing"""

import urllib

from bs4 import BeautifulSoup


def get_dolphin_html():
    url = 'https://dolphin-emu.org/download/'
    response = urllib.request.urlopen(url)
    data = response.read()
    return data.decode('utf-8')


def get_dolphin_link(dolphin_html=None):
    if dolphin_html is None:
        dolphin_html = get_dolphin_html()

    soup = BeautifulSoup(dolphin_html, "html.parser")
    return soup.find_all('a', {"class": 'btn always-ltr btn-info win'}, limit=1, href=True)[0]['href']


def get_dolphin_changelog(dolphin_html=None):
    if dolphin_html is None:
        dolphin_html = get_dolphin_html()

    text = ""
    soup = BeautifulSoup(dolphin_html, "html.parser")
    sections = soup.find('table', {"class": 'versions-list dev-versions'})
    for section in sections.find_all('tr', {"class": 'infos'}):
        version = section.find("td", {"class": "version"}).find("a").get_text()
        reldate = section.find("td", {"class": "reldate"}).get_text()
        change = section.find("td", {"class": "description"}).get_text()
        text += version + " - " + reldate + ":\n" + change + "\n\n"

    return text
