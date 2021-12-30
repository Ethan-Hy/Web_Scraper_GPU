# This is a web scraping script which will
# compare graphical processing unit card prices from various different websites.
from bs4 import BeautifulSoup
import requests
import re
from playwright.sync_api import sync_playwright
from time import sleep

# User must specify if they want an AMD or Nvidia GPU as some websites separate them out
input_track = True
while input_track:
    brand = input("Do you want to search for an AMD or Nvidia GPU?")
    if brand.lower() == "amd" or brand.lower() == "nvidia":
        input_track = False
    else:
        input_track = True
product = input("What product do you want to search for?")

# initialise dictionary where all GPUs found will be stored
items_found = {}


# newegg.com
# url = f"https://www.newegg.com/global/uk-en/p/pl?d={product}" - generic search.
# Search specifically for graphics cards
url = f"https://www.newegg.com/global/uk-en/p/pl?d={product}&N=101582767&isdeptsrh=1"
page = requests.get(url).text
doc = BeautifulSoup(page, "html.parser")

# find number of pages to search through them all
page_text = doc.find(class_="list-tool-pagination-text").strong
pages = int(str(page_text).split("/")[-2].split(">")[-1][:-1])


for page in range(1, pages + 1):
    url = f"https://www.newegg.com/global/uk-en/p/pl?d={product}&N=101582767&isdeptsrh=1&page={page}"
    page = requests.get(url).text
    doc = BeautifulSoup(page, "html.parser")

    # items grid
    div = doc.find(class_="item-cells-wrap border-cells items-grid-view four-cells expulsion-one-cell")
    # find text with searched product terms
    items = div.find_all(text=re.compile(product))
    for item in items:
        parent = item.parent

        # sometimes there is an issue with text not being the one shown on the website
        # check if in parent <a> to ensure it is correct as it will contain a link to the product
        if parent.name != "a":
            continue

        next_parent = item.find_parent(class_="item-container")
        # checks if the item is out of stock
        if next_parent.find(class_="item-promo"):
            continue
        link = parent['href']
        price_pound = next_parent.find(class_="price-current").strong.string
        price_pence = next_parent.find(class_="price-current").sup.string
        price = price_pound + price_pence
        items_found[item] = {"price": float(price.replace(",", "")), "link": link}


# ebuyer.com
# url = f"https://www.ebuyer.com/search?q={product}" - generic search
# search specifically for graphics cards
if brand.lower() == "nvidia":
    url = f"https://www.ebuyer.com/store/Components/cat/Graphics-Cards-Nvidia?q={product}"
else:
    url = f"https://www.ebuyer.com/store/Components/cat/Graphics-Cards-AMD?q={product}"
page = requests.get(url).text
doc = BeautifulSoup(page, "html.parser")

# find number of pages to search through them all.
# number of pages not shown so need to calculate it from number of products shown and available to view.
page_text = doc.find(class_="showing-count")
pages_text = str(page_text).split("of")
if len(pages_text) > 1:
    items_page = int(pages_text[0].replace(" ", "").split("-")[2])
    total_items = int(pages_text[1].replace(" ", "").split("r")[0])
    pages = (total_items + (items_page - 1))//items_page
else:
    pages = int(pages_text[0].split(" ")[2])
for page in range(1, pages + 1):
    if brand.lower() == "nvidia":
        url = f"https://www.ebuyer.com/store/Components/cat/Graphics-Cards-Nvidia?page={page}&q={product}"
    else:
        url = f"https://www.ebuyer.com/store/Components/cat/Graphics-Cards-AMD?page={page}&q={product}"

    page = requests.get(url).text
    doc = BeautifulSoup(page, "html.parser")

    # only items within grid
    div = doc.find(class_="grid-view js-taxonomy-view is-active")
    # find any text with searched product terms
    items = div.find_all(text=re.compile(product))
    for item in items:
        parent = item.parent
        if parent.name != "a":
            continue
        next_parent = item.find_parent(class_="grid-item js-listing-product")
        # checks if the item is out of stock
        if next_parent.find(class_="grid-item__coming-soon"):
            continue
        link = parent['href']
        link = "https://www.ebuyer.com" + link
        price = next_parent.find(class_="grid-item__price").find(text=re.compile(" "))
        item = str(item).strip()
        price = price.strip()
        items_found[item] = {"price": float(price.replace(",", "")), "link": link}


sorted_items = sorted(items_found.items(), key=lambda x: x[1]['price'])

for item in sorted_items:
    print(item[0])
    print(f"£{item[1]['price']}")
    print(item[1]['link'])
    print("------------------------------------------------------------------------------------------------------------"
          "-----------------------------------------------------------")