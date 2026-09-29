import requests
import pandas as pd
import csv
from bs4 import BeautifulSoup

#Tech Crunch URL
articles_url = "https://techcrunch.com/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

#Scraper api parameters
payload = {
    "api_key": "63920ac42c1873ca3e2696e7df4ba2ea",
    "url": articles_url
}

#Make a request to the scraper API
response = requests.get("https://api.scraperapi.com", params=payload)
response.raise_for_status()  # Raise an exception for HTTP errors

#Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

articles = soup.select('div.loop-card')

print(f"Found {len(articles)} articles.\n")