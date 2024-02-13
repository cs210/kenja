"""
Simple recommendation algorithm for wine
"""
from bs4 import BeautifulSoup
import requests

class WineInfo:
    def __init__(self, comments, wine_rating):
        self.comments = comments
        self.wine_rating = wine_rating

# highest number: 4911810?
def discover_num_wines():
    index = 1 # index 0 is a wine not found error
    while True:
        website = "https://www.cellartracker.com/notes.asp?iWine="
        website += str(index)
        print(website)
        x = requests.get(website)
        print(x.status_code)
        while True:
            if x.status_code != 202:
                break
        if (x.status_code != 200):
            print("Error with status code: ", x.status_code,)
            print("Error occurred on value: ", index)
            break
        print(index)
        index += 1000000


def scrape_notes(website):
    """
    Scrape CellarTracker page for notes.
    """
    x = requests.get(website)

    html = x.text
    soup = BeautifulSoup(html, features="html.parser")
    print(soup.prettify())

if __name__ == "__main__":
    scrape_notes('https://www.cellartracker.com/notes.asp?iWine=3')
    # discover_num_wines()
    