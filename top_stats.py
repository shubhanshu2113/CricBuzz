import streamlit as st
import pandas as pd
from utils import get_stats_list, fetch_stats

def show():
    st.header("🌟 Top Players Stats")

    # ✅ Fetch available stat categories
    stats_options = get_stats_list() or {}
    stats_types = stats_options.get("statsTypesList", []) or []

    if not stats_types:
        st.warning("⚠️ No stat types available from the API.")
        return

    # Extract available categories (Batting / Bowling)
    categories = [cat.get("category") for cat in stats_types]
    category = st.selectbox("🎯 Choose Category", categories)

    # Get stat types for chosen category
    selected_cat = next((c for c in stats_types if c.get("category") == category), {})
    stat_mapping = {s.get("header"): s.get("value") for s in selected_cat.get("types", [])}

    # Select stat type
    stat_header = st.selectbox("📊 Choose Stat Type", ["--Select--"] + list(stat_mapping.keys()))

    if stat_header == "--Select--":
        st.info("Select a stat type to fetch top players.")
        return

    stat_value = stat_mapping[stat_header]

    if st.button("Fetch Top Players"):
        try:
            # ✅ Call API with only stat type (no format)
            data = fetch_stats(stat_value, "") or {}

            headers = data.get("headers") or []
            players = data.get("values") or data.get("stats") or []

            table_rows = []
            for p in players:
                if isinstance(p, dict) and "values" in p:
                    row = list(p["values"])
                    # 🚨 Drop first column if it's playerId
                    if row and str(row[0]).isdigit():
                        row = row[1:]
                elif isinstance(p, dict):
                    row = list(p.values())
                elif isinstance(p, (list, tuple)):
                    row = list(p)
                else:
                    row = [p]
                table_rows.append(row)

            if not table_rows:
                st.warning("⚠️ API returned no player rows for this selection.")
                return

            # Make sure header count matches row length
            max_len = max(len(r) for r in table_rows)
            if not headers or len(headers) < max_len:
                headers = headers + [f"Col{i+1}" for i in range(len(headers), max_len)]

            normalized_rows = []
            for r in table_rows:
                if len(r) > len(headers):
                    normalized_rows.append(r[:len(headers)])
                elif len(r) < len(headers):
                    normalized_rows.append(r + [""] * (len(headers) - len(r)))
                else:
                    normalized_rows.append(r)

            df = pd.DataFrame(normalized_rows, columns=headers)

            st.success(f"Showing top players for **{stat_header}** in **{category}**")
            st.table(df.head(10))

        except Exception as e:
            st.error(f"Error fetching or processing stats: {e}")
