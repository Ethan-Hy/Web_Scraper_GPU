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



