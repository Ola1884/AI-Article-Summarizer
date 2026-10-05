import json
import os
from scraper import scrape_latest_articles
from cleaner import clean_text
from summarizer import summarize_article


def run_pipeline(num_articles=3, output_file="output/summaries.json"):
    # 1. Scrape
    print("Step 1: Scraping articles...")
    articles = scrape_latest_articles(num_articles)
    print(f"   Got {len(articles)} articles.\n")

    # 2. Clean + Summarize each article
    print("Step 2: Cleaning and summarizing...")
    results = []
    for i, article in enumerate(articles):
        print(f"   [{i+1}/{len(articles)}] {article['Title']}")

        # Clean the content
        cleaned_content = clean_text(article['Content'])

        # Summarize the cleaned content
        summary = summarize_article(cleaned_content)

        results.append({
            "Title": article['Title'],
            "URL": article['URL'],
            "Author": article['Author'],
            "Published Date": article['Published Date'],
            "Original Length": len(cleaned_content),
            "Summary": summary,
            "Summary Length": len(summary)
        })

    # 3. Save results
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"\nSaved {len(results)} summaries to {output_file}")
    return results


if __name__ == "__main__":
    run_pipeline(num_articles=3)