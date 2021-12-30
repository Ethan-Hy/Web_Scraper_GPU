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


# overclockers.co.uk
# can fail to reach server due to cloudflare so try up to 4 times
for x in range(0, 4):
    error = True

    # url = f"https://www.overclockers.co.uk/search?sSearch={product}" - generic search
    # search specifically for pc components
    url = f"https://www.overclockers.co.uk/search/index/sSearch/" \
          f"{product}/sFilter_category/PC+Components/sSort/3/sPerPage/12"

    # get past cloudflare
    # https://stackoverflow.com/questions/65604551/cant-bypass-cloudflare-with-python-cloudscraper
    with sync_playwright() as p:
        browser = p.webkit.launch()
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(10000)
        doc = BeautifulSoup(page.content(), "html.parser")
        browser.close()

    # find number of pages to search through them all
    page_text = doc.find(class_="display_sites").contents
    pages = int(page_text[7].string)
    for page in range(1, pages + 1):
        url = f"https://www.overclockers.co.uk/search/index/sSearch/" \
              f"{product}/sFilter_category/PC+Components/sSort/6/sPerPage/12/sPage/{page}"
        with sync_playwright() as p:
            browser = p.webkit.launch()
            page = browser.new_page()
            page.goto(url)
            page.wait_for_timeout(10000)
            doc = BeautifulSoup(page.content(), "html.parser")
            browser.close()
        # only items
        div = doc.find(class_="listing")
        # find any text with searched product terms
        # items = div.find_all(text=re.compile(product))
        items = div.find_all(class_="producttitles", title=re.compile(product))
        for item in items:
            link = item['href']
            parent = item.find_parent(class_="inner")
            price = parent.find(class_="price")

            # check if out of stock
            if price is None:
                continue
            price = float(price.find(text=re.compile("£")).replace("£", "").replace(",", "").strip())
            items_found[item['title']] = {"price": price, "link": link}
    error = False
    if error:
        sleep(2)  # wait 2 seconds if failed
    else:
        break



sorted_items = sorted(items_found.items(), key=lambda x: x[1]['price'])

for item in sorted_items:
    print(item[0])
    print(f"£{item[1]['price']}")
    print(item[1]['link'])
    print("------------------------------------------------------------------------------------------------------------"
          "-----------------------------------------------------------")