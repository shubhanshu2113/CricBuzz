import streamlit as st
import sqlite3
import pandas as pd

DB_PATH = "cricbuzz_livestats/cricket.db"

def run_query(query, params=(), commit=False):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    if commit:
        conn.commit()
        conn.close()
        return None
    else:
        cols = [desc[0] for desc in cur.description]
        # Deduplicate column names
        seen, fixed_cols = {}, []
        for col in cols:
            if col not in seen:
                seen[col] = 0
                fixed_cols.append(col)
            else:
                seen[col] += 1
                fixed_cols.append(f"{col}_{seen[col]}")

        df = pd.DataFrame(cur.fetchall(), columns=fixed_cols)
        conn.close()
        return df

def show():
    st.header("⚙️ Cricket Database CRUD Operations")

    menu = ["View Records", "Insert Record", "Update Record", "Delete Record"]
    choice = st.selectbox("📌 Select Action", menu)

    # --- VIEW RECORDS ---
    if choice == "View Records":
        st.subheader("📋 View Records")
        table = st.selectbox("Select Table", ["matches", "scores", "teams", "players", "player_stats"])

        df = run_query(f"SELECT * FROM {table}")
        st.dataframe(df)

    # --- INSERT RECORD ---
    elif choice == "Insert Record":
        st.subheader("➕ Insert New Record")
        table = st.selectbox("Select Table", ["teams", "player_stats"])

        if table == "teams":
            team_id = st.number_input("Team ID", min_value=1)
            team_name = st.text_input("Team Name")
            team_sname = st.text_input("Team Short Name")

            if st.button("Insert"):
                run_query(
                    "INSERT INTO teams (team_id, team_name, team_sname) VALUES (?, ?, ?)",
                    (team_id, team_name, team_sname),
                    commit=True
                )
                st.success("✅ Team record inserted successfully!")

        elif table == "player_stats":
            stat_type = st.text_input("Stat Type")
            category = st.text_input("Category")
            player_name = st.text_input("Player Name")
            matches = st.number_input("Matches", min_value=0)
            innings = st.number_input("Innings", min_value=0)
            runs = st.number_input("Runs", min_value=0)
            average = st.number_input("Average", min_value=0.0)
            strike_rate = st.number_input("Strike Rate", min_value=0.0)

            if st.button("Insert"):
                run_query(
                    """INSERT INTO player_stats 
                    (player_id, player_name, format, scope, matches, innings, runs, average) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (player_id, player_name, format, scope, matches, innings, runs, average),
                    commit=True
                )
                st.success("✅ Player stat inserted successfully!")

    # --- UPDATE RECORD ---
    elif choice == "Update Record":
        st.subheader("✏️ Update Record")
        table = st.selectbox("Select Table", ["teams", "player_stats"])

        if table == "teams":
            df = run_query("SELECT * FROM teams")
            st.dataframe(df)

            team_id = st.number_input("Enter Team ID to Update", min_value=1)
            new_name = st.text_input("New Team Name")
            new_sname = st.text_input("New Short Name")

            if st.button("Update"):
                run_query(
                    "UPDATE teams SET team_name=?, team_sname=? WHERE team_id=?",
                    (new_name, new_sname, team_id),
                    commit=True
                )
                st.success("✅ Team updated successfully!")

        elif table == "player_stats":
            df = run_query("SELECT rowid, * FROM player_stats")
            st.dataframe(df)

            rowid = st.number_input("Enter Row ID to Update", min_value=1)
            new_runs = st.number_input("New Runs", min_value=0)
            new_avg = st.number_input("New Average", min_value=0.0)

            if st.button("Update"):
                run_query(
                    "UPDATE player_stats SET runs=?, average=? WHERE rowid=?",
                    (new_runs, new_avg, rowid),
                    commit=True
                )
                st.success("✅ Player stats updated successfully!")

    # --- DELETE RECORD ---
    elif choice == "Delete Record":
        st.subheader("🗑️ Delete Record")
        table = st.selectbox("Select Table", ["teams", "player_stats"])

        if table == "teams":
            df = run_query("SELECT * FROM teams")
            st.dataframe(df)

            team_id = st.number_input("Enter Team ID to Delete", min_value=1)
            if st.button("Delete"):
                run_query("DELETE FROM teams WHERE team_id=?", (team_id,), commit=True)
                st.success("✅ Team deleted successfully!")

        elif table == "player_stats":
            df = run_query("SELECT rowid, * FROM player_stats")
            st.dataframe(df)

            rowid = st.number_input("Enter Row ID to Delete", min_value=1)
            if st.button("Delete"):
                run_query("DELETE FROM player_stats WHERE rowid=?", (rowid,), commit=True)
                st.success("✅ Player stat deleted successfully!")







