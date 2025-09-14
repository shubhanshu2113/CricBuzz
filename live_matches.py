import streamlit as st
from utils import fetch_live_matches, save_match_to_db, show_live_match

def show():   # 👈 this function MUST exist
    st.header("📺 Live Matches")
    data = fetch_live_matches()

    for match_type in data.get("typeMatches", []):
        for series in match_type.get("seriesMatches", []):
            series_data = series.get("seriesAdWrapper", {})
            for match in series_data.get("matches", []):
                match_info = match.get("matchInfo")
                match_score = match.get("matchScore")
                save_match_to_db(match_info, match_score)
                show_live_match(match)
                st.markdown("---")

