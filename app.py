"""
Main interface for the Sommelier app.
"""

# Stuff for Streamlit -- comment out for now
# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Main packages to import
import streamlit as st
from helpers.book_rec_helpers import find_match
from helpers.metrics import SEARCH_COUNT
from helpers.state import count_sessions

# Header + increment visit count
count_sessions()
st.title("📚🐛 Bookworm")
st.subheader(
    "Looking for a new read? Just tell us what you're looking to dive in next!"
)

# Core form/search function
submitted = False
slider_val = ""
with st.form("input_form"):
    st.write("Describe what type of book you're looking for below:")
    slider_val = st.text_input('Ex: "I want a book that is about magic."')

    # Submit function
    submitted = st.form_submit_button("Submit")

# Checking for submitted + increment count
if submitted:
    SEARCH_COUNT.inc()
    st.subheader("Recommendations")
    results = find_match(slider_val)

    # Display results
    for i in range(len(results["documents"][0])):
        metadata = results["metadatas"][0][i]
        print(metadata)
        st.write("## 📘 [" + metadata["title"] + "](" + metadata["link"] + ")")
        score_str = ""
        for i in range(int(metadata["score"])):
            score_str += "⭐️"
        st.write("### " + score_str)
        st.write(metadata["description"])
        st.write("**Publisher:** " + metadata["publisher"])
        st.write("**Publication date:** " + metadata["publication_date"])
        st.divider()
