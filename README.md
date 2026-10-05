# ⚡ ZapRead — AI Article Summarizer

An end-to-end NLP pipeline that scrapes the latest articles from TechCrunch, cleans the raw text, and generates concise AI-powered summaries using Hugging Face's `facebook/bart-large-cnn`.

Includes an interactive **Streamlit** web app and a **command-line** pipeline for batch processing.

---

## ✨ Features

- **Web scraping** — Extracts the latest 3–5 articles from TechCrunch using BeautifulSoup
- **Bot bypass** — Routes requests through ScraperAPI to avoid anti-bot protection
- **Ad filtering** — Skips inline advertisements by inspecting parent HTML classes
- **Metadata extraction** — Title, author, published date, and word count
- **Text cleaning** — Normalizes whitespace, quotes, and removes junk phrases
- **Smart chunking** — Splits long articles into overlapping chunks to respect BART's 1024-token limit
- **AI summarization** — Uses `facebook/bart-large-cnn` with hierarchical (chunk → combine → re-summarize) pipeline
- **Interactive UI** — Streamlit app with sidebar navigation, tabbed views, and export options
- **Error handling** — Retries on connection errors, logs HTML structure changes, and stores all failures persistently
- **Export** — Download results as `.txt` or `.md`

---

## 📁 Project Structure

AI-Article-Summarizer/
├── .gitignore
├── .env # API keys (not committed)
├── README.md
├── requirements.txt
│
├── scraper.py # Scraping + retries + error logging
├── cleaner.py # Text normalization
├── summarizer.py # BART chunked summarization
├── error_log.py # Error persistence module
│
├── app.py # Web UI (main entry point) using streamlit
├── pipeliner.py # CLI entry point (batch processing)
└── output/
├── summaries.json
└── error_log.json # Auto-generated on first error


---

## 🚀 Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/AI-Article-Summarizer.git
cd AI-Article-Summarizer
