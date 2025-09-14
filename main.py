import streamlit as st
from utils import init_db

# Import your page modules
from pages import home, live_matches, top_stats, sql_queries, crud_operations

# Initialize DB
init_db()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["🏠 Home", "📺 Live Matches", "🌟 Top Players", "📊 SQL Queries", "🛠️ CRUD Operations"])

# Route pages
if page == "🏠 Home":
    home.show()

elif page == "📺 Live Matches":
    live_matches.show()

elif page == "🌟 Top Players":
    top_stats.show()

elif page == "📊 SQL Queries":
    sql_queries.show()

elif page == "🛠️ CRUD Operations":
    crud_operations.show()





