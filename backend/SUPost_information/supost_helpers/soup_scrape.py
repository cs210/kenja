import requests
from bs4 import BeautifulSoup


# Function to scrape a single page
def scrape_page(url):
    response = requests.get(url, allow_redirects=False)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        # Extract names of items
        item_names = [
            a.text.strip() for a in soup.select("div.listing-item a.listing-item-title")
        ]
        return item_names
    else:
        print("Failed to fetch page:", url)
        return []


# Function to scrape multiple pages
def scrape_multiple_pages(base_url, num_pages):
    all_item_names = []
    for page_num in range(1, num_pages + 1):
        url = f"{base_url}?page={page_num}"
        item_names = scrape_page(url)
        all_item_names.extend(item_names)
    return all_item_names


# URL of the website
base_url = "https://supost.com/search/cat/5"
# Number of pages to scrape
num_pages = 3

# Scrape multiple pages
item_names = scrape_multiple_pages(base_url, num_pages)

# Print the scraped item names
for i, name in enumerate(item_names, start=1):
    print(f"{i}. {name}")
