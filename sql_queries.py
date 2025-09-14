import streamlit as st
import sqlite3
import pandas as pd
from utils import load_players_from_json, save_venue_to_db, load_matches_from_json, insert_player_stats_from_topstats


DB_PATH = "cricbuzz_livestats/cricket.db"

# Utility to run SQL queries
def run_sql_query(query: str):
    """Execute SQL query on cricket.db and return results as DataFrame"""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        conn.close()
        raise e
    conn.close()
    return df


def show():
    st.title("🗂️ SQL Queries Dashboard")

    # ---------------- Data Loader Section ----------------
    st.subheader("📥 Load JSON Data into Database")

    if st.button("Load Players JSON"):
        load_players_from_json("all_team_players.json")
        st.success("✅ Players data loaded into DB!")

    if st.button("Load Matches JSON"):
        load_matches_from_json("recent_matches.json")
        st.success("✅ Matches data loaded into DB!")

    if st.button("Load Venues JSON"):
        save_venue_to_db("all_venues.json")
        st.success("✅ Venues data loaded into DB!")


    st.divider()

    # --- queries ---
    queries = {
        "Q1. Players from India": """
            SELECT p.full_name, p.batting_style, p.bowling_style, t.team_id
            FROM players p
            JOIN teams t
            ON p.team_id = t.team_id
            WHERE p.team_id = 2; -- team_id 2 means india
        """,

        "Q2. Matches in last 30 days": """
            SELECT 
                m.match_desc,
                m.team1_name AS team1,
                m.team2_name AS team2,
                v.venue_name,
                v.city,
                datetime(m.start_date / 1000, 'unixepoch') AS match_start,
                datetime(m.end_date   / 1000, 'unixepoch') AS match_end
            FROM matches m
            LEFT JOIN teams t1 ON m.team1_id = t1.team_id
            LEFT JOIN teams t2 ON m.team2_id = t2.team_id
            LEFT JOIN venues v ON m.venue_id = v.venue_id
            WHERE date(m.start_date / 1000, 'unixepoch') >= date('now', '-30 days')
            ORDER BY m.start_date DESC;
        """,

        "Q3. Top 10 ODI run scorers": """
            SELECT p.full_name,
                   s.runs,
                   s.average
            FROM player_stats s
            JOIN players p ON p.player_id = s.player_id
            WHERE s.format = 'test'
            ORDER BY s.runs DESC
            LIMIT 10;
        """,

        "Q4. Venues with capacity > 50k": """
            SELECT venue_name, city, country, capacity
            FROM venues
            WHERE CAST(REPLACE(capacity, ',', '') AS INTEGER) > 50000
            ORDER BY CAST(REPLACE(capacity, ',', '') AS INTEGER) DESC;
        """,

        "Q5. Matches won by each team": """
                        SELECT
                            team_name,
                            COUNT(*) AS wins
                        FROM (
                            SELECT
                                CASE
                                    WHEN m.status LIKE '%won by%' THEN
                                        CASE
                                            WHEN INSTR(m.status, m.team1_name) > 0 THEN m.team1_name
                                            WHEN INSTR(m.status, m.team2_name) > 0 THEN m.team2_name
                                            ELSE NULL
                                        END
                                    ELSE NULL
                                END AS team_name
                            FROM
                                matches m
                            WHERE
                                m.state = 'Complete'
                                AND m.status LIKE '%won by%'
                        ) AS subquery
                        WHERE team_name IS NOT NULL
                        GROUP BY
                            team_name
                        ORDER BY
                            wins DESC;
        """,

        "Q6. Players per playing role": """
            SELECT playing_role, COUNT(*) AS total_players
            FROM players
            GROUP BY playing_role
            ORDER BY total_players DESC;
        """,

        "Q7. Highest individual score per format": """
            SELECT format,
                   MAX(runs) AS highest_score
            FROM player_stats
            GROUP BY format;
        """,

        "Q8. Series that started in 2024": """
            SELECT series_name, host_country, match_type, start_date, total_matches
            FROM series
            WHERE strftime('%Y', start_date) = '2024'
            ORDER BY date(start_date);
        """,

        "Q9. All-rounders >1000 runs & >50 wickets": """
            SELECT p.full_name,
                SUM(COALESCE(pfs.runs,0)) AS total_runs,
                SUM(COALESCE(pfs.wickets,0)) AS total_wickets,
                pfs.format
            FROM player_stats pfs
            JOIN players p ON p.player_id = pfs.player_id
            GROUP BY pfs.player_id, pfs.format
            HAVING SUM(COALESCE(pfs.runs,0)) > 1000
            AND SUM(COALESCE(pfs.wickets,0)) > 50
            ORDER BY total_runs DESC;
        """,

        "Q10. Last 20 completed matches (most recent first)": """
            SELECT m.match_desc,
                m.team1_name AS team1,
                m.team2_name AS team2,
                wt.team_name AS winning_team,
                -- Extract victory margin and type from status when possible, else NULL
                CASE
                    WHEN instr(lower(m.status), 'won by') > 0 THEN
                    trim(substr(m.status, instr(lower(m.status),'won by') + 6))
                    ELSE NULL
                END AS victory_margin_and_type,
                v.venue_name
            FROM matches m
            LEFT JOIN teams t1 ON t1.team_id = m.team1_id
            LEFT JOIN teams t2 ON t2.team_id = m.team2_id
            LEFT JOIN teams wt ON wt.team_id = m.winner_team_id
            LEFT JOIN venues v ON v.venue_id = m.venue_id
            WHERE m.state = 'Complete'
            ORDER BY datetime(m.end_date) DESC
            LIMIT 20;
        """,

        "Q11. Player performance across formats (players who played >=2 formats)": """
            WITH per_format AS (
                SELECT p.player_id,
                    p.full_name,
                    pfs.format,
                    SUM(COALESCE(pfs.runs,0)) AS runs_in_format,
                    AVG(COALESCE(pfs.batting_avg, NULL)) AS avg_in_format
                FROM player_format_stats pfs
                JOIN players p ON p.player_id = pfs.player_id
                GROUP BY p.player_id, pfs.format
            ),
            formats_count AS (
                SELECT player_id, COUNT(DISTINCT format) AS formats_played
                FROM per_format
                GROUP BY player_id
                HAVING formats_played >= 2
            )
            SELECT pf.player_id,
                pf.full_name,
                MAX(CASE WHEN pf.format = 'test' THEN pf.runs_in_format END) AS test_runs,
                MAX(CASE WHEN pf.format = 'odi'  THEN pf.runs_in_format END) AS odi_runs,
                MAX(CASE WHEN pf.format = 't20'  THEN pf.runs_in_format END) AS t20_runs,
                -- overall batting average across formats weighted by matches if available
                ROUND(
                    (SUM(COALESCE(pfs.runs,0)) * 1.0) /
                    NULLIF(SUM(COALESCE(pfs.matches,0)),0)
                ,2) AS overall_avg_runs_per_match
            FROM per_format pf
            JOIN formats_count fc ON fc.player_id = pf.player_id
            LEFT JOIN player_format_stats pfs ON pfs.player_id = pf.player_id
            GROUP BY pf.player_id, pf.full_name
            ORDER BY overall_avg_runs_per_match DESC;
        """,

        "Q12. Team home vs away performance (wins count)": """
        -- Assumes teams.country & venues.country exist. A match is 'home' for team if team's country == venue.country
            WITH match_results AS (
                SELECT m.match_id,
                    m.winner_team_id,
                    m.match_format,
                    m.team1_id,
                    m.team2_id,
                    v.country AS venue_country
                FROM matches m
                LEFT JOIN venues v ON v.venue_id = m.venue_id
                WHERE m.state = 'Complete'
            ),
            team_matches AS (
                SELECT mr.match_id,
                    t.team_id,
                    t.team_name,
                    CASE
                    WHEN t.team_id = mr.team1_id THEN 'team1'
                    WHEN t.team_id = mr.team2_id THEN 'team2'
                    END AS side,
                    CASE WHEN t.country = mr.venue_country THEN 'home' ELSE 'away' END AS home_away,
                    CASE WHEN mr.winner_team_id = t.team_id THEN 1 ELSE 0 END AS is_win
                FROM match_results mr
                JOIN teams t ON t.team_id IN (mr.team1_id, mr.team2_id)
            )
            SELECT team_id, team_name,
                SUM(CASE WHEN home_away = 'home' THEN is_win ELSE 0 END) AS home_wins,
                SUM(CASE WHEN home_away = 'away' THEN is_win ELSE 0 END) AS away_wins,
                SUM(CASE WHEN home_away = 'home' THEN 1 ELSE 0 END) AS total_home_matches,
                SUM(CASE WHEN home_away = 'away' THEN 1 ELSE 0 END) AS total_away_matches
            FROM team_matches
            GROUP BY team_id, team_name
            ORDER BY (home_wins + away_wins) DESC;
        """,

        "Q13. Partnerships >=100 runs (consecutive batting positions)": """
        -- Assumes partnerships table has consecutive batting partners logged (player1_id, player2_id) per innings
            SELECT pt.match_id,
                pt.innings_id,
                p1.full_name AS batsman_1,
                p2.full_name AS batsman_2,
                pt.runs AS partnership_runs
            FROM partnerships pt
            JOIN players p1 ON p1.player_id = pt.player1_id
            JOIN players p2 ON p2.player_id = pt.player2_id
            WHERE pt.runs >= 100
            ORDER BY pt.runs DESC, pt.match_id;
        """,

        "Q14. Bowlers performance at venues (>=3 matches at same venue, >=4 overs per match)": """
        -- Assumes bowling(player_id, match_id, venue_id, overs, runs_conceded, wickets)
            WITH bowler_venue AS (
                SELECT b.player_id, b.venue_id,
                    COUNT(DISTINCT b.match_id) AS matches_played,
                    SUM(b.wickets) AS total_wickets,
                    SUM(b.runs_conceded) AS total_runs_conceded,
                    SUM(b.overs) AS total_overs
                FROM bowling b
                GROUP BY b.player_id, b.venue_id
                HAVING matches_played >= 3
                    AND MIN(b.overs) >= 4   -- ensure bowled at least 4 overs in each match; if MIN not supported, adjust logic
            )
            SELECT bv.player_id,
                    pl.full_name,
                    bv.venue_id,
                    v.venue_name,
                    bv.matches_played,
                    bv.total_wickets,
                    ROUND((bv.total_runs_conceded * 1.0) / NULLIF(bv.total_overs,0), 2) AS avg_economy
            FROM bowler_venue bv
            JOIN players pl ON pl.player_id = bv.player_id
            JOIN venues v ON v.venue_id = bv.venue_id
            ORDER BY avg_economy ASC, total_wickets DESC;
        """,

        "Q15. Players in close matches (<50 runs OR <5 wickets) performance": """
            WITH close_matches AS (
                SELECT match_id,
                    -- infer margin: try parse 'won by X runs' or 'won by Y wkts'
                    CASE
                        WHEN instr(lower(status),'won by') > 0 AND instr(lower(status),'runs') > 0 THEN
                            CAST(trim(substr(lower(status), instr(lower(status),'won by')+7, instr(lower(status),'runs') - instr(lower(status),'won by') -7)) AS INTEGER)
                        WHEN instr(lower(status),'won by') > 0 AND instr(lower(status),'wkts') > 0 THEN
                            -CAST(trim(substr(lower(status), instr(lower(status),'won by')+7, instr(lower(status),'wkts') - instr(lower(status),'won by') -7)) AS INTEGER)
                        ELSE NULL
                    END AS margin_signed,
                    winner_team_id
                FROM matches
                WHERE state = 'Complete'
            ), filtered AS (
                SELECT cm.match_id, cm.winner_team_id
                FROM close_matches cm
                WHERE (cm.margin_signed IS NOT NULL AND (abs(cm.margin_signed) < 50 OR cm.margin_signed BETWEEN -4 AND 4))
            ), player_vs_close AS (
                SELECT bs.player_id,
                    bs.match_id,
                    bs.runs,
                    CASE WHEN m.winner_team_id = bs.team_id THEN 1 ELSE 0 END AS team_won_when_batted
                FROM batting bs
                JOIN matches m ON m.match_id = bs.match_id
                WHERE bs.match_id IN (SELECT match_id FROM filtered)
            )
            SELECT p.player_id,
                    p.full_name,
                    ROUND(AVG(player_vs_close.runs),2) AS avg_runs_in_close,
                    COUNT(DISTINCT player_vs_close.match_id) AS total_close_matches,
                    SUM(player_vs_close.team_won_when_batted) AS team_wins_when_batted
            FROM player_vs_close
            JOIN players p ON p.player_id = player_vs_close.player_id
            GROUP BY p.player_id, p.full_name
            HAVING total_close_matches > 0
            ORDER BY avg_runs_in_close DESC;
        """,


    }

    # --- Choose query to run ---
    query_choice = st.selectbox("Choose a query to run", list(queries.keys()))

    if st.button("▶️ Run Query"):
        query = queries[query_choice]
        try:
            df = run_sql_query(query)
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ No results found.")
        except Exception as e:
            st.error(f"Error running query: {e}")


if __name__ == "__main__":
    show()



















