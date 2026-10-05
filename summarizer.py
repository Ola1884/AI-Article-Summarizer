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
            chunks.append(" ".join(current_chunk))
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
        chunks.append(" ".join(current_chunk))
    return chunks



def summarize_chunk(chunk,compression_ratio=0.2,hard_max=250,hard_min=30):
    """
    Summarizes a chunk of text.

    compression_ratio: target summary length as a fraction of the input tokens
    hard_max: absolute upper bound on summary length (prevent runaway output)
    hard_min: absolute lower bound on summary length (prevent one-word summaries)
    """
    inputs = tokenizer(chunk,return_tensors="pt",max_length=1024,truncation=True).to(model.device)

    input_length = inputs["input_ids"].shape[1]
    target_length = int(input_length * compression_ratio)
    max_len = max(hard_min,min(target_length,hard_max)) # max is min of target and hard max, but at least hard min
    min_len = max(10,int(max_len*0.4)) # min is ~40% of max

    summary_ids = model.generate(
        inputs["input_ids"],
        attention_mask=inputs["attention_mask"],   
        max_length=max_len,
        min_length=min_len,
        length_penalty = 1.5,
        num_beams=5,
        no_repeat_ngram_size = 3,
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
    combine = " ".join(chunk_summarizes)
    # Summarize all the chunk summaries into a final summary
    final_summary = summarize_chunk(combine, compression_ratio=0.3, hard_max=200, hard_min=60)
    return final_summary



if __name__ == "__main__":
    # Example usage
    article_text = "Your long article text goes here..."
    summary = summarize_article(article_text)
    print("Summary:")
    print(summary)