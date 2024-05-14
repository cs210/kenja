from selenium import webdriver
from bs4 import BeautifulSoup
import csv


def extract_post_text(soup):
    # Find the div element with class "post-text"
    post_text_div = soup.find("div", class_="post-text")
    # If the div element is found, extract the text content
    if post_text_div:
        return post_text_div.get_text(separator="\n").strip()
    else:
        return None


def extract_post_title(soup):
    # Find the h2 element with class "forsale"
    post_title_h2 = soup.find("h2", class_="forsale")
    # If the h2 element is found, extract the title
    if post_title_h2:
        return post_title_h2.get_text(separator=" ").strip()
    else:
        return None


def extract_post_date(soup):
    # Find the div element with class "item-date"
    item_date_div = soup.find("div", class_="item-date")
    # If the div element is found, extract the date
    if item_date_div:
        # Find the span element inside the div
        date_span = item_date_div.find("span")
        # If the span element is found, extract the date text
        if date_span:
            return date_span.get_text(strip=True)
    return None


def extract_post_price(soup):
    # Find the div element with class "item-date"
    item_date_div = soup.find("div", class_="item-price")
    # If the div element is found, extract the date
    if item_date_div:
        # Find the span element inside the div
        date_span = item_date_div.find("span")
        # If the span element is found, extract the date text
        if date_span:
            return date_span.get_text(strip=True)
    return None


# Initialize the Selenium WebDriver in headless mode
options = webdriver.ChromeOptions()
options.add_argument("headless")
driver = webdriver.Chrome(options=options)
writefile = "supostdata422.csv"
fields = ["Title", "Description", "Price", "Date"]

with open(writefile, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()

    for i in range(1):
        if i == 0:
            pg = ""
        else:
            pg = "?page=" + str(i + 1)
        url = "https://supost.com/search/cat/5" + pg

        # Fetch the page content with Selenium
        driver.get(url)
        page_source = driver.page_source

        soup = BeautifulSoup(page_source, "html.parser")

        posts = soup.find_all("div", class_="one-result")

        # Go through each post on page
        for post in posts:
            post_link = post.find("a", class_="post-link")["href"]
            full_url = "https://supost.com" + post_link
            driver.get(full_url)
            page_src = driver.page_source
            sp = BeautifulSoup(page_src, "html.parser")
            contents = {
                "Title": extract_post_title(sp),
                "Description": extract_post_text(sp),
                "Price": extract_post_price(sp),
                "Date": extract_post_date(sp),
            }
            writer.writerow(contents)

driver.quit()
