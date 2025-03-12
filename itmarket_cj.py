from app import fetch_all_jobs
from transformers import pipeline
from datetime import datetime
import sqlite3, torch

# Load a local summarization model (e.g., BART or T5)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=0 if torch.cuda.is_available() else -1)

# Max token length the model can handle
MAX_INPUT_LENGTH = 1024  # Change this to your model's max token length

def chunk_text(text, max_length=MAX_INPUT_LENGTH):
    """Chunks a long text into smaller parts that fit within the model's max token length."""
    # Split text into sentences (or you can use other methods if needed)
    sentences = text.split('\n')
    chunked_text = []
    current_chunk = []

    for sentence in sentences:
        # Add sentence to the chunk if it does not exceed max length
        if len(' '.join(current_chunk + [sentence])) < max_length:
            current_chunk.append(sentence)
        else:
            # Otherwise, start a new chunk
            chunked_text.append(' '.join(current_chunk))
            current_chunk = [sentence]

    # Add the last chunk if it contains any remaining text
    if current_chunk:
        chunked_text.append(' '.join(current_chunk))

    return chunked_text

def summarize_titles_with_local_model(data):
    # Extract only the job titles
    titles = [job['title'] for job in data]

    # Prepare the job titles to summarize
    prompt = "Summarize the following job titles to understand the job market trends:\n"
    
    # Add all job titles to the prompt
    prompt += "\n".join(titles)

    # Chunk the text into smaller parts
    chunks = chunk_text(prompt, max_length=MAX_INPUT_LENGTH)
    
    summaries = []
    for chunk in chunks:
        try:
            # Summarize each chunk of job titles
            summary = summarizer(chunk, max_length=150, min_length=50, do_sample=False)
            summaries.append(summary[0]['summary_text'])
            print(f"Generated Summary for chunk: {summary[0]['summary_text']}")
        except Exception as e:
            print(f"Error summarizing chunk: {e}")
            summaries.append("Error generating summary.")
    
    # Combine all summaries into a final result
    final_summary = " ".join(summaries)
    return final_summary

def fetch_and_store_data():
    conn = sqlite3.connect('itjobs_analysis.db')
    c = conn.cursor()
    
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS itjobs_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_count INTEGER,
            analysis_text TEXT,
            date TEXT
        )
    ''')
    
    conn.commit()

    # Fetch the job data
    data = fetch_all_jobs()

    # Check if the fetched data is a list (as expected)
    if isinstance(data, list):
        # Analyze with the local summarization model (only job titles)
        analysis_text = summarize_titles_with_local_model(data)

        # Insert the job count for today and the analysis text into the database
        c.execute(''' 
            INSERT INTO itjobs_analysis (offer_count, analysis_text, date) 
            VALUES (?, ?, ?)
        ''', (len(data), analysis_text, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        # Commit and close the connection
        conn.commit()
    else:
        print("Error: fetched data is not in the expected format.")

    conn.close()

if __name__ == "__main__":
    fetch_and_store_data()
