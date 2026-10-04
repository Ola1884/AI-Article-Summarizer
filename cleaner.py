import re

def clean_text(text):
    # clean articles raw text 
    if not text or text == "NA":
        return text

    # 1. replace non-breaking spaces with regular spaces
    text = text.replace('\xa0', ' ')

    # 2. replace smart quotes with regular quotes
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")

    # 3. replace em-dashes and en-dashes with regular dashes
    text = text.replace('—', '-').replace('–', '-')

    # 4. remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # 5. remove any remaining non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', '', text)

    # 6. collapse more than 2 newlines into just 2
    text = re.sub(r'\n{3,}','\n\n',text)

    # 7. remove common junk phrases that survive scraping
    junk_phrases = [
        "Read more",
        "Read More",
        "Sign up for our newsletter",
        "Subscribe to our newsletter",
        "Follow us on",
    ]
    for phrase in junk_phrases:
        text = text.replace(phrase,"")

    # 8. remove leading or trailing whitespaces
    text = text.strip()

    return text

if __name__ == "__main__":
    text =""
    cleaned_text = clean_text(text)
    print(f"Cleaned text: {cleaned_text}")