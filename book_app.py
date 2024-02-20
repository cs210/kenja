"""
Main interface for the Sommelier app.
"""
# Stuff for Streamlit -- comment out for now
# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Main packages to import
import streamlit as st
from book_rec_helpers import *
from metrics import SEARCH_COUNT
from state import count_sessions

# Header + increment visit count
count_sessions()
st.title("📚 Book Finder")
st.subheader("You give us a request, we give you book recs.")

# Core form/search function
submitted = False
slider_val = ""
with st.form("input_form"):
   st.write("Describe what type of book you're looking for...")
   slider_val = st.text_input("Ex: \"I want a book that is about magic.\"")

   # Submit function
   submitted = st.form_submit_button("Submit")

# Checking for submitted + increment count
if submitted:
    SEARCH_COUNT.inc()
    st.subheader("Recommendations")
    results = find_match(slider_val)

    # Display results
    for i in range(len(results['documents'][0])):
        metadata = results['metadatas'][0][i]
        st.write("📘 " + metadata['title'])
        st.write("Description: " + metadata['description'])
        st.write("score: " + str(round(metadata['score'],1)))
        st.write("publisher: " + metadata['publisher'])
        st.write("publication date: " + metadata['publication_date'])
        st.write("Link to buy: " + metadata['link'])
        st.divider()