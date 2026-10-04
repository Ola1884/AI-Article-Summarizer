from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import nltk
nltk.download('punkt',quiet=True)

tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn", device_map="auto")

def chunk_text(text,tokenizer,max_tokens=900,overlap_tokens=100):
    """
    Splits a long text into overlapping chunks based on sentences.
    max_tokens: size of each chunk (must be < model's 1024 limit)
    overlap_tokens: overlap between chunks to preserve context
    """
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0

    # Iterate through sentences and create chunks
    for sentence in sentences:
        # Count the number of tokens in the sentence
        sentence_tokens = len(tokenizer.encode(sentence,add_special_tokens=False))
        # If adding this sentence exceeds the max_tokens limit, finalize the current chunk and start a new one
        if current_length + sentence_tokens > max_tokens:
            chunks.append("".join(current_chunk))
            # Start a new chunk with overlap
            overlap_sentences = []
            overlap_length = 0
            # Add sentences from the end of the current chunk to the new chunk until we reach the overlap limit
            for sent in reversed(current_chunk):
                # Count the number of tokens in the sentence
                sent_len = len(tokenizer.encode(sent, add_special_tokens=False))
                # If adding this sentence exceeds the overlap_tokens limit, stop adding sentences
                if overlap_length + sent_len > overlap_tokens:
                    break
                # Add the sentence to the overlap list and update the overlap length
                overlap_sentences.insert(0, sent)
                overlap_length += sent_len
            # Start the new chunk with the overlap sentences
            current_chunk = overlap_sentences + [sentence]
            current_length = overlap_length + sentence_tokens

        # If adding this sentence does not exceed the max_tokens limit, add it to the current chunk
        current_chunk.append(sentence)
        current_length += sentence_tokens

    # Add the last chunk if it has content
    if current_chunk:
        chunks.append("".join(current_chunk))
    return chunks



def summarize_chunk(chunk,max_length=150,min_length=40):
    # Summarizes a single chunk of text using the BART model.
    inputs = tokenizer(chunk,return_tensor="pt",max_length=1024,truncation=True).to(model.device)
    summary_ids = model.generate(
        inputs["input_ids"],
        max_length=max_length,
        min_length=min_length,
        length_penalty = 2.0,
        num_beams=4,
        early_stopping=True
        )
    return tokenizer.decode(summary_ids[0],skip_special_tokens=True)


def summarize_article(article_text):
    # Summarizes the input text using the BART model.
    #1. Chunk text
    chunks = chunk_text(article_text,tokenizer,max_tokens=900,overlap_tokens=100)
    print(f"Split article into {len(chunks)} chunks")

    #2. Summarize each chunk
    chunk_summarizes = [summarize_chunk(c) for c in chunks]

    #3. If one chunk found return directly
    if len(chunk_summarizes) == 1:
        return chunk_summarizes[0]
    combine = "".join(chunk_summarizes)
    # Summarize all the chunk summaries into a final summary
    final_summary = summarize_chunk(combine,max_length=200,min_lenght=60)
    return final_summary



if __name__ == "__main__":
    # Example usage
    article_text = "Your long article text goes here..."
    summary = summarize_article(article_text)
    print("Summary:")
    print(summary)