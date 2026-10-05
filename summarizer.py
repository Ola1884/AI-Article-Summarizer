from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import nltk
import os
from error_log import log_error

# Suppress symlink warning on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Download NLTK data on first run
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

# Load model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn", device_map="auto")


def chunk_text(text, tokenizer, max_tokens=900, overlap_tokens=100):
    """
    Splits a long text into overlapping chunks based on sentences.
    max_tokens: size of each chunk (must be < model's 1024 limit)
    overlap_tokens: overlap between chunks to preserve context
    """
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_tokens = len(tokenizer.encode(sentence, add_special_tokens=False))

        if current_length + sentence_tokens > max_tokens:
            chunks.append(" ".join(current_chunk))

            # Build overlap from end of previous chunk
            overlap_sentences = []
            overlap_length = 0
            for sent in reversed(current_chunk):
                sent_len = len(tokenizer.encode(sent, add_special_tokens=False))
                if overlap_length + sent_len > overlap_tokens:
                    break
                overlap_sentences.insert(0, sent)
                overlap_length += sent_len

            current_chunk = overlap_sentences + [sentence]
            current_length = overlap_length + sentence_tokens
            continue

        current_chunk.append(sentence)
        current_length += sentence_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def summarize_chunk(chunk, target_length=150, hard_max=350, hard_min=40):
    """
    Summarizes a single chunk. `target_length` is in TOKENS.
    Produces output between ~60% and 100% of the effective max length.
    """
    try:
        inputs = tokenizer(
            chunk,
            return_tensors="pt",
            max_length=1024,
            truncation=True,
        ).to(model.device)

        input_length = inputs["input_ids"].shape[1]

        # Allow summaries up to 50% of the input length
        max_by_input = max(hard_min, int(input_length * 0.5))
        effective_max = min(target_length, hard_max, max_by_input)

        # Force the model to produce at least 60% of the max
        effective_min = max(20, int(effective_max * 0.6))

        summary_ids = model.generate(
            inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=effective_max,
            min_length=effective_min,
            length_penalty=1.0,
            num_beams=5,
            no_repeat_ngram_size=3,
            early_stopping=True,
        )
        return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    except Exception as e:
        log_error(
            context="summarizer.summarize_chunk",
            error_type="inference",
            message=str(e),
        )
        return ""


def summarize_article(article_text, target_length=200):
    """
    Full pipeline: chunk → summarize each chunk → summarize the summaries.

    `target_length` is in WORDS (matching the UI slider). It's converted
    to tokens internally using the 1 word ≈ 1.3 tokens approximation.
    """
    if not article_text or article_text == "N/A":
        return "N/A"

    # Convert words → tokens
    target_tokens = int(target_length * 1.3)

    chunks = chunk_text(article_text, tokenizer, max_tokens=900, overlap_tokens=100)
    print(f"Split article into {len(chunks)} chunk(s)")

    if not chunks:
        return "N/A"

    # Single chunk: summarize directly
    if len(chunks) == 1:
        return summarize_chunk(chunks[0], target_length=target_tokens)

    # Multiple chunks: distribute target, then combine
    per_chunk_target = max(60, target_tokens // len(chunks))
    chunk_summaries = [
        summarize_chunk(c, target_length=per_chunk_target) for c in chunks
    ]

    combined = " ".join(s for s in chunk_summaries if s)
    if not combined.strip():
        return "N/A"

    final_summary = summarize_chunk(
        combined,
        target_length=target_tokens,
        hard_max=target_tokens + 100,
        hard_min=max(50, target_tokens // 2),
    )
    return final_summary


if __name__ == "__main__":
    # Quick test
    article_text = "Your long article text goes here. " * 50
    summary = summarize_article(article_text, target_length=200)
    print("Summary:")
    print(summary)