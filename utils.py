import sqlite3
import requests
import streamlit as st
import json
import os

API_KEY = "46fbf1ceedmsh16f5991ffb1d123p1c0680jsn26f84197b93f"
HOST = "cricbuzz-cricket.p.rapidapi.com"

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": HOST
}

# ✅ Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Make sure data dir exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ----------------- DB Initialization -----------------
def init_db():
    conn = sqlite3.connect("cricbuzz_livestats/cricket.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        match_id INTEGER PRIMARY KEY,
        series_id INTEGER,
        series_name TEXT,
        match_desc TEXT,
        match_format TEXT,
        start_date TEXT,
        end_date TEXT,
        state TEXT,
        status TEXT,
        team1_id INTEGER,
        team1_name TEXT,
        team2_id INTEGER,
        team2_name TEXT,
        venue TEXT,
        city TEXT,
        venue_id INTEGER,
        timezone TEXT,
        team_id INTEGER,
        FOREIGN KEY (venue_id) REFERENCES venues (venue_id),
        FOREIGN KEY (series_id) REFERENCES series (series_id),
        FOREIGN KEY (team_id) REFERENCES teams (team_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        match_id INTEGER,
        team_id INTEGER,
        innings_id INTEGER,
        runs INTEGER,
        wickets INTEGER,
        overs REAL,
        FOREIGN KEY (match_id) REFERENCES matches (match_id),
        FOREIGN KEY (team_id) REFERENCES series (series_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        team_id INTEGER PRIMARY KEY,
        team_name TEXT,
        team_sname TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        player_id INTEGER PRIMARY KEY,
        full_name TEXT,
        image_id TEXT,
        batting_style TEXT,
        bowling_style TEXT,
        team_id INTEGER,
        playing_role TEXT,
        FOREIGN KEY (team_id) REFERENCES teams (team_id)
    )
    """)


    # series
    cur.execute("""
    CREATE TABLE IF NOT EXISTS series (
        series_id INTEGER PRIMARY KEY,
        series_name TEXT,
        start_date TEXT,
        end_date TEXT,
        month_group TEXT
    )
    """)

    # Series player statistics
    cur.execute("""
    CREATE TABLE IF NOT EXISTS series_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        series_id INTEGER,
        format TEXT,
        player_id INTEGER,
        player_name TEXT,
        matches INTEGER,
        innings INTEGER,
        runs INTEGER,
        average REAL,
        FOREIGN KEY (series_id) REFERENCES series (series_id),
        FOREIGN KEY (player_id) REFERENCES players (player_id)
    )
    """)


    #venues
    cur.execute("""
    CREATE TABLE IF NOT EXISTS venues (
        venue_id INTEGER PRIMARY KEY AUTOINCREMENT,
        venue_name TEXT,
        city TEXT,
        country TEXT,
        timezone TEXT,
        established INTEGER,
        capacity INTEGER,
        alt_name TEXT,
        end_names TEXT,
        home_teams TEXT,
        floodlights BOOLEAN,
        curator TEXT,
        profile TEXT,
        image_url TEXT,
        image_id TEXT,
        FOREIGN KEY (venue_id) REFERENCES matches (venue_id)
    )
    """)

    # stats
    cur.execute("""
    CREATE TABLE IF NOT EXISTS player_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        player_name TEXT,
        format TEXT,        
        scope TEXT,         
        series_id INTEGER,  
        matches INTEGER,
        innings INTEGER,
        runs INTEGER,
        average REAL,
        FOREIGN KEY (player_id) REFERENCES players(player_id),
        FOREIGN KEY (series_id) REFERENCES series(series_id)
    )
    """)

    conn.commit()
    conn.close()

def fetch_live_matches():
    url = f"https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {}

def get_stats_list():
    url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/topstats"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {}

def fetch_stats(stats_type, format_type):
    url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/topstats/0"
    params = {"statsType": stats_type, "formatType": format_type}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json() 
    else:
        return {}

# ----------------- JSON Loaders -----------------
def load_players_from_json(file_name="all_team_players.json"):
    conn = sqlite3.connect("cricbuzz_livestats/cricket.db")
    cur = conn.cursor()
    
    file_path = os.path.join(DATA_DIR, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        players = json.load(f)

    for player in players:
        # Skip category headers like "BATSMEN", "ALL ROUNDER" etc. (they have no "id")
        if "id" not in player:
            continue  

        player_id = int(player["id"])
        full_name = player.get("name")
        image_id = player.get("img_id")
        batting_style = player.get("battingStyle")
        bowling_style = player.get("bowlingStyle")
        team_id = player.get("team_id")
        playing_role = player.get("playing_role")


        # Insert into players table
        cur.execute("""
            INSERT OR IGNORE INTO players 
            (player_id, full_name, image_id, batting_style, bowling_style, team_id, playing_role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            player_id,
            full_name,
            image_id,       
            batting_style,
            bowling_style,
            team_id,
            playing_role
        ))

        # Insert into teams if needed (team_id is known)
        if team_id:
            team_name = player.get("teamName") or None
            team_sname = player.get("teamSName") or None
            cur.execute("""
                INSERT OR IGNORE INTO teams (team_id, team_name, team_sname)
                VALUES (?, ?, ?)
            """, (team_id, team_name, team_sname))  # can update with proper names later

    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(players)} players from {file_path}")


def get_venues_stats(venue_id: int):
    url = f"https://cricbuzz-cricket2.p.rapidapi.com/venues/v1/27"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        {}

def get_venues_stats(venue_id: int):
    """Fetch details of a single venue by its ID"""
    url = f"https://cricbuzz-cricket.p.rapidapi.com/venues/v1/{venue_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {}

def get_all_venues():
    """Fetch list of all venues with IDs"""
    url = f"https://cricbuzz-cricket.p.rapidapi.com/venues/v1/all"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("venueList", [])
    else:
        return []

def save_venue_to_db(file_name="all_venues.json"):
    """Insert a single venue into the DB"""
    
    conn = sqlite3.connect("cricbuzz_livestats/cricket.db")
    cur = conn.cursor()

    file_path = os.path.join(DATA_DIR, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        venues = json.load(f)
    # Clean capacity field
    for venue_info in venues:
        capacity_int = None
        if venue_info.get("capacity"):
            try:
                capacity_int = int(str(venue_info.get("capacity")).replace(",", ""))
            except (ValueError, TypeError):
                pass
            
        cur.execute("""
            INSERT OR IGNORE INTO venues 
            (venue_name, city, country, timezone, established, capacity, alt_name, end_names, home_teams, floodlights, curator, profile, image_url, image_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            venue_info.get("ground"),
            venue_info.get("city"),
            venue_info.get("country"),
            venue_info.get("timezone"),
            venue_info.get("established"),
            capacity_int,
            venue_info.get("knownAs"),
            venue_info.get("ends"),
            venue_info.get("homeTeam"),
            venue_info.get("floodlights"),
            venue_info.get("curator"),
            venue_info.get("profile"),
            venue_info.get("imageUrl"),
            venue_info.get("imageId")
        ))
    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(venues)} venues from {file_path}")

def seed_all_venues():
    """Fetch all venues and insert them into DB"""
    venues = get_all_venues()
    for v in venues:
        venue_id = v.get("id")
        if venue_id:
            details = get_venues_stats(venue_id)
            save_venue_to_db(details)
    print(f"✅ Inserted {len(venues)} venues into DB")

# ------player_stats---------
def insert_player_stats_from_topstats(file_name="player_stats.json"):
    """
    Load player stats from JSON into the player_stats table.
    JSON must come from the topstats API script.
    """
    conn = sqlite3.connect("cricbuzz_livestats/cricket.db")
    cur = conn.cursor()

    file_path = os.path.join(DATA_DIR, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        stats_data = json.load(f)

    inserted_count = 0

    for stat_type, block in stats_data.items():
        if not isinstance(block, dict):
            continue 
             
        headers = block.get("headers", [])
        values = block.get("values", [])

        for row in values:
            if not isinstance(row, dict):
                continue 
            vals = row.get("values", [])
            if not vals or len(vals) < 2:
                continue

            player_id = None
            try:
                if vals[0].isdigit():
                    player_id = int(vals[0])
            except Exception:
                pass

            

            # player_id sometimes missing → set None
            player_name = vals[1] if len(vals) > 1 else None

            matches = int(vals[2]) if len(vals) > 2 and vals[2].isdigit() else None
            innings = int(vals[3]) if len(vals) > 3 and vals[3].isdigit() else None
            runs = int(vals[4]) if len(vals) > 4 and vals[4].isdigit() else None

            try:
                average = float(vals[5]) if len(vals) > 5 else None
            except ValueError:
                average = None

            cur.execute("""
                INSERT OR IGNORE INTO player_stats
                (player_id, player_name, format, scope, series_id, matches, innings, runs, average)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player_id,
                player_name,
                block.get("filter", {}).get("selectedMatchType"),
                stat_type,
                None,   # series_id not available in topstats API
                matches,
                innings,
                runs,
                average
            ))
            inserted_count += 1

    conn.commit()
    conn.close()
    print(f"✅ Inserted {inserted_count} rows from {file_path} into player_stats")


# for matches
def load_matches_from_json(file_name="recent_matches.json"):
    conn = sqlite3.connect("cricbuzz_livestats/cricket.db")
    cur = conn.cursor()

    file_path = os.path.join(DATA_DIR, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    match_count, score_count = 0, 0

    # Walk through nested structure
    for type_block in data.get("typeMatches", []):
        for series in type_block.get("seriesMatches", []):
            series_wrapper = series.get("seriesAdWrapper", {})
            for m in series_wrapper.get("matches", []):
                match_info = m.get("matchInfo", {})
                match_score = m.get("matchScore", {})

                # Insert into matches table
                cur.execute("""
                    INSERT OR REPLACE INTO matches 
                    (match_id, series_id, series_name, match_desc, match_format, start_date, end_date, state, status,
                     team1_id, team1_name, team2_id, team2_name, venue, city)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    match_info.get("matchId"),
                    match_info.get("seriesId"),
                    match_info.get("seriesName"),
                    match_info.get("matchDesc"),
                    match_info.get("matchFormat"),
                    match_info.get("startDate"),
                    match_info.get("endDate"),
                    match_info.get("state"),
                    match_info.get("status"),
                    match_info.get("team1", {}).get("teamId"),
                    match_info.get("team1", {}).get("teamName"),
                    match_info.get("team2", {}).get("teamId"),
                    match_info.get("team2", {}).get("teamName"),
                    match_info.get("venueInfo", {}).get("ground"),
                    match_info.get("venueInfo", {}).get("city")
                ))
                match_count += 1

                # Insert scores if present
                for team_key in ["team1Score", "team2Score"]:
                    team_score = match_score.get(team_key, {})
                    for inng in team_score.values():
                        cur.execute("""
                            INSERT OR REPLACE INTO scores 
                            (match_id, team_id, innings_id, runs, wickets, overs)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            match_info.get("matchId"),
                            match_info.get(team_key.replace("Score", ""), {}).get("teamId"),
                            inng.get("inningsId"),
                            inng.get("runs"),
                            inng.get("wickets"),
                            inng.get("overs")
                        ))
                        score_count += 1

    conn.commit()
    conn.close()
    print(f"✅ Inserted {match_count} matches and {score_count} scores from {file_path}")

# ----------------------------------------------------
def save_match_to_db(match_info, match_score):
    if not match_info or not match_score:
        return

    conn = sqlite3.connect("cricbuzz_livestats/cricket.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO matches 
        (match_id, series_id, series_name, match_desc, match_format, start_date, end_date, state, status, team1_id, team1_name, team2_id, team2_name, venue, city, venue_id, timezone, team_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        match_info.get("matchId"),
        match_info.get("seriesId"),
        match_info.get("seriesName"),
        match_info.get("matchDesc"),
        match_info.get("matchFormat"),
        match_info.get("startDate"),
        match_info.get("endDate"),
        match_info.get("state"),
        match_info.get("status"),
        match_info.get("team1", {}).get("team1Id"),
        match_info.get("team1", {}).get("teamName"),
        match_info.get("team2", {}).get("team2Id"),
        match_info.get("team2", {}).get("teamName"),
        match_info.get("venueInfo", {}).get("ground"),
        match_info.get("venueInfo", {}).get("city"),
        match_info.get("venueInfo", {}).get("id"),
        match_info.get("venueInfo", {}).get("timezone"),
        match_info.get("teamInfo", {}).get("team_id")
    ))

    for team_key, team_info in [("team1Score", "team1"), ("team2Score", "team2")]:
        team_score = match_score.get(team_key, {})
        for inng in team_score.values():
            cur.execute("""
                INSERT INTO scores (match_id, team_id, innings_id, runs, wickets, overs)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                match_info.get("matchId"),
                match_info.get(team_info, {}).get("teamId"),
                inng.get("inningsId"),
                inng.get("runs"),
                inng.get("wickets"),
                inng.get("overs")
            ))

    conn.commit()
    conn.close()


# ----------------- UI Helper -----------------
def show_live_match(match):
    match_info = match.get("matchInfo", {})
    match_score = match.get("matchScore", {})

     # ✅ Series name & match details
    series_name = match_info.get("seriesName", "Unknown Series")
    match_desc = match_info.get("matchDesc", "")
    match_format = match_info.get("matchFormat", "")

    st.subheader(f"{series_name} - {match_desc} ({match_format})")

    venue = match_info.get("venueInfo", {}).get("ground", "Unknown Venue")
    city = match_info.get("venueInfo", {}).get("city", "")
    status = match_info.get("status", "Status not available")

    st.markdown(f"📍 **Venue:** {venue}, {city}")
    st.markdown(f"📊 **Status:** {status}")

    for team_key, team_info in [("team1Score", "team1"), ("team2Score", "team2")]:
        team_score = match_score.get(team_key)
        if team_score:
            team_data = match_info.get(team_info, {})
            team_name = team_data.get("teamName", f"Team {team_data.get('teamId')}")
            for _, inng in team_score.items():
                runs = inng.get("runs", 0)
                wickets = inng.get("wickets", 0)
                overs = inng.get("overs", 0.0)
                st.markdown(f"**{team_name}:** {runs}/{wickets} in {overs} overs")

























