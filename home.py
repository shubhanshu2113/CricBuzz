import streamlit as st

def show():
    st.title("🏏 Cricbuzz Live Stats - Home Page")

    # --- Project Description ---
    st.header("📌 Project Overview")
    st.markdown("""
    The **Cricbuzz Live Stats** project provides real-time cricket insights by 
    integrating the **Cricbuzz API** with **SQLite database** and **Streamlit dashboards**.  
    It allows users to:
    - View **live matches** and scores  
    - Explore **player and team statistics**  
    - Query the database with **SQL queries**  
    - Perform **CRUD operations** on cricket data  
    - Analyze **venues and series**  
    """)

    # --- Tools Used ---
    st.header("🛠 Tools & Technologies")
    st.markdown("""
    - **Python** (Data processing & API integration)  
    - **Streamlit** (Interactive dashboard)  
    - **SQLite3** (Database for storing cricket data)  
    - **Pandas** (Data manipulation)  
    - **Cricbuzz API (RapidAPI)** (Data source)  
    """)

    # --- Navigation Instructions ---
    st.header("📂 Navigation")
    st.markdown("""
    Use the **left sidebar** to switch between different pages:
    - 🏠 **Home Page** → Project intro & instructions  
    - 📊 **Live Matches** → View live match details  
    - 🌟 **Top Players Stats** → Explore batting & bowling records  
    - 🗂 **SQL Queries** → Run SQL queries on cricket data  
    - ✏️ **CRUD Operations** → Insert, update, and delete records    
    """)

    # --- Project Documentation ---
    st.header("📄 Project Documentation")
    st.markdown("""
    📘 [Click here to view full project report](cricbuzz_livestats/project_report.pdf)  
    """)

    # --- Folder Structure ---
    st.header("📁 Project Folder Structure")
    st.code("""
    cricbuzz_livestats/
    ├── main.py
    ├── utils.py
    ├── pages/
    │   ├── home.py
    │   ├── live_matches.py
    │   ├── top_stats.py
    │   ├── sql_queries.py
    │   ├── crud_operations.py
    ├── data/
    │   ├── all_team_players.json
    │   ├── all_venues.json
    │   ├── recent_matches.json
    │   ├── player_stats.json
    ├── cricket.db
    └── Project_report.pdf
    """)

    st.success("✅ Welcome! Use the sidebar to explore cricket stats.")




