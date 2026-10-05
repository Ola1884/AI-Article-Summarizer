import re


def clean_text(text):
    """
    Cleans raw article text by removing common scraping artifacts
    while PRESERVING paragraph breaks (double newlines).
    """
    if not text or text == "N/A":
        return text

    # 1. Normalize non-breaking spaces
    text = text.replace('\xa0', ' ')

    # 2. Normalize smart quotes to ASCII
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('‘', "'").replace('’', "'")

    # 3. Normalize em/en dashes
    text = text.replace('—', ' - ').replace('–', ' - ')

    # 4. Collapse repeated SPACES and TABS only — NOT newlines
    #    (this preserves \n\n paragraph breaks)
    text = re.sub(r'[ \t]+', ' ', text)

    # 5. Collapse 3+ newlines into exactly 2 (single paragraph break)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 6. Remove common junk phrases
    junk_phrases = [
        "Read more",
        "Read More",
        "Sign up for our newsletter",
        "Subscribe to our newsletter",
        "Follow us on",
    ]
    for phrase in junk_phrases:
        text = text.replace(phrase, "")

    # 7. Strip leading/trailing whitespace
    text = text.strip()

    return text