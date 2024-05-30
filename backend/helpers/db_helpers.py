"""
Helper functions for tracking metrics like searches for B2B side.
"""
from datetime import datetime
import sqlite3

# Constants
DB_NAME = "db/data.db"

def create_db():
    """
    Create database and initial tables, if not already done.
    """
    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create searches table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS searches (
        id INTEGER PRIMARY KEY,
        query TEXT,
        latency FLOAT,
        date TEXT,
        time TEXT
    )
    ''')

def add_query(query, latency, timestamp):
    """
    Add a search query entry to the database.
    """
    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Split up the timestamp
    dt = datetime.fromisoformat(timestamp)
    date_str = dt.strftime("%-m/%-d/%Y")
    time_str = dt.strftime("%-I:%M %p")
    
    # Add information to the table
    cursor.execute('''
    INSERT INTO searches (query, latency, date, time) VALUES (?, ?, ?, ?)
    ''', (query, latency, date_str, time_str))
    
    # Commit the transaction and close
    conn.commit()
    conn.close()
    
def total_queries():
    """
    Get the total number of search queries in the database.
    """
    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Query the total number of entries
    cursor.execute('SELECT COUNT(*) FROM searches')
    result = cursor.fetchone()[0]
    
    # Close the connection
    conn.close()
    return result

def queries_per_timestamp():
    """
    Get the number of search queries per timestamp.
    """
    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Query the number of entries per timestamp
    cursor.execute('SELECT date, COUNT(*) FROM searches GROUP BY date')
    result = cursor.fetchall()
    
    # Close the connection
    conn.close()
    return result

def read_all_rows():
    """
    Read all the existing rows from the database.
    """
    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Query all rows
    cursor.execute('SELECT * FROM searches')
    result = cursor.fetchall()
    
    # Close the connection
    conn.close()
    return result