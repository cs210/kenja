"""
Simple recommendation algorithm for wine
"""
from bs4 import BeautifulSoup
import requests

def scrape_notes(website):
    """
    Scrape CellarTracker page for notes.
    """
    x = requests.get(website)
    html = x.text
    soup = BeautifulSoup(html)
    print(soup.prettify())

if __name__ == "__main__":
    scrape_notes('https://www.cellartracker.com/notes.asp?iWine=3')
    