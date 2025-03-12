from app import fetch_all_jobs
import sqlite3, datetime

def fetch_and_store_data():
    conn = sqlite3.connect("itjobs_daily.db")
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data (
        job_count INTEGER,
        date TEXT PRIMARY KEY
    )
    """)
    
    today = datetime.date.today().isoformat()
    
    # Check if data for today already exists
    cursor.execute("SELECT * FROM data WHERE date = ?", (today,))
    if cursor.fetchone():
        return
    
    # Insert the job count for today
    cursor.execute("INSERT INTO data VALUES (?, ?)", (len(fetch_all_jobs()), today))
    conn.commit()
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    fetch_and_store_data()
