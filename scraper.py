import requests
import pandas as pd
import csv
from bs4 import BeautifulSoup
import time
from datetime import datetime


#Tech Crunch URL
articles_url = "https://techcrunch.com/"
API_KEY = ""

def get_article_content(url):

    #Scraper api parameters
    payload = {
        "api_key": API_KEY,
        "url": url
    }
    try:
        response = requests.get("https://api.scraperapi.com", params=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors

        content_soup = BeautifulSoup(response.content, "html.parser")

        #find the main article container
        article_container = content_soup.find('div', class_='entry-content')
        if not article_container:
            return "N/A"
        all_paragraphs = article_container.find_all('p',class_="wp-block-paragraph")

        cleaned_paragraphs = []
        for p in all_paragraphs:
            # check if parent has ad class skip this paragraph
            is_ad = False
            for parent in p.parents:
                parent_classes = parent.get('class', [])
                if 'tc-event-inline-cta' in parent_classes or 'hb-modal-container' in parent_classes:
                    is_ad = True
                    break
            if is_ad:
                continue
            text = p.get_text(strip=True)
            if text:  # Only add non-empty paragraphs
                cleaned_paragraphs.append(text)
        return "\n\n".join(cleaned_paragraphs) if cleaned_paragraphs else "N/A"
                    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching article content: {e}")
        return "N/A"

    
payload = {
    "api_key": API_KEY,
    "url": articles_url
}
#Make a request to the scraper API
response = requests.get("https://api.scraperapi.com", params=payload)
response.raise_for_status()  # Raise an exception for HTTP errors

#Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

#find latest news section
latest_section = soup.find('div', class_='latest-news-section')
if not latest_section:
    print("❌ Could not find the Latest News section container!")
    exit()

articles = latest_section.select('div.loop-card')
scraped_articles = []
for idx,article in enumerate(articles):
    print(f"Scraping article {idx + 1}...")
    title_tag = article.select_one('a.loop-card__title-link')
    title = title_tag.get_text(strip=True) if title_tag else 'N/A'
    link_tag = article.select_one('a.loop-card__title-link')
    url = link_tag['href'] if link_tag else 'N/A'
    author_tag = article.select_one('a.loop-card__author')
    author = author_tag.get_text(strip=True) if author_tag else 'N/A'
    time_tag = article.find('time', class_='loop-card__time')
    published_date = time_tag.get('datetime') if time_tag else "N/A"

    if url != 'N/A':
        content = get_article_content(url)
    else:
        content = "N/A"
    article_data = {
        "Title": title,
        "URL": url,
        "Author": author,
        "Published Date": published_date,
        "Content": content
    }
    scraped_articles.append(article_data)
valid = [a for a in scraped_articles if a['Published Date'] != "N/A"]
latest_3_articles = sorted(valid, key=lambda x: datetime.fromisoformat(x['Published Date']), reverse=True)[:3]
time.sleep(1)  # Sleep for 1 second between requests to avoid overwhelming the server 


print("\n" + "="*60)
print("RESULTS")
print("="*60 + "\n")

for i, article in enumerate(latest_3_articles):
    print(f"Article {i+1}:")
    print(f"Title: {article['Title']}")
    print(f"URL: {article['URL']}")
    print(f"Author: {article['Author']}")
    print(f"Published Date: {article['Published Date']}")
    preview = article['Content']
    print(f"Content Preview: {preview}\n")
