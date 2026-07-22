import streamlit as st
import pandas as pd
from datetime import datetime

from src.api import get_kalshi_data, get_polymarket_data

st.set_page_config(page_title="The field", page_icon="🏈", layout="wide")

st.title("The field: Live tracking")

tab_main, tab_xp = st.tabs(["Live odds", "xPoints"])

with tab_main:
    settings = st.columns([1, 2, 2, 1])
    columns = st.columns(3)

with settings[0]:
    odds_provider = st.pills("Odds source", ["Kalshi", "Polymarket"], default="Kalshi", required=True, key="odds_pills", help="Kalshi/Polymarket merge in development...")

with settings[1]:
    selected_players = st.pills("Players", ["Krish", "Lucas", "Martin", "Thomas", "Tommy"], key="players_pills", selection_mode="multi")

with settings[2]:
    hide_unpicked = st.toggle("Hide unpicked teams/players", value=True)

fetch_fn = get_polymarket_data if odds_provider == "Polymarket" else get_kalshi_data
market_id_col = "polymarket_slug" if odds_provider == "Polymarket" else "kalshi_ticker"
leagues = pd.read_csv("data/leagues.csv").sort_values("end_date").reset_index(drop=True)
draft = pd.read_csv("data/Sports Draft - Draft.csv").sort_values("pick").reset_index(drop=True)

with st.spinner(f"Fetching {odds_provider} odds..."):
    odds = []
    for i, league in leagues.iterrows():

        try:
            df = fetch_fn(league[market_id_col]).sort_values(by="prob", ascending=False)
            df = df[df["prob"] > 0]
            df["league"] = league["league_name"]
            st.space("small")
        except Exception as e:
            # st.error(f"Failed to fetch {odds_provider} odds.")
            continue
        odds.append(df)

    odds = pd.concat(odds).reset_index(drop=True) if odds else pd.DataFrame()

    odds_and_picks = odds.merge(draft, on=["team", "league"], how="outer")
    odds_and_picks["player_name"] = odds_and_picks["player_name"].fillna("--")
    odds_and_picks["prob"] = odds_and_picks["prob"].fillna(0.)

# st.dataframe(odds_and_picks)


for i, league in leagues.iterrows():

    picks = odds_and_picks.copy()[odds_and_picks["league"] == league["league_name"]].reset_index(drop=True)

    field_odds = 100 - picks[picks["player_name"] != "--"]["prob"].sum()
    field_idx = picks.query("team == 'The field'").index[0]
    picks.at[field_idx, "prob"] = field_odds

    picks = picks.sort_values(["prob", "team"], ascending=[False, True])

    with columns[i % 3]:

        container = st.container(height=500, gap="xxsmall")
        with container:

            st.write(league["league_name"])
            st.caption(datetime.strftime(datetime.strptime(league["end_date"], "%Y-%m-%d"), "%B %Y"))
#             # try:
#             #     df = fetch_fn(league[market_id_col]).sort_values(by="prob", ascending=False)
#             #     df = df.copy()[df["prob"] > 0]
#             #     st.space("small")
#             # except Exception as e:
#             #     st.error(f"Failed to fetch {odds_provider} odds.")
#             #     continue

            if picks.empty:
                st.warning(f"No {odds_provider} odds found for this league.")
                continue

            if selected_players:
                picks = picks[picks["player_name"].isin(selected_players)]
            if hide_unpicked:
                picks = picks[picks["player_name"] != "--"]

            tm_col, pick_col, prob_col = st.columns([2, 1, 1])
            for _, row in picks.iterrows():
                with tm_col:
                    st.write(row["team"])
                with pick_col:
                    # pick_str = f" {row['player_name']} <sup>#{int(row['pick'])}</sup>" if not pd.isna(row['pick']) else "--"
                    # pick_str = f"<sup>#{int(row['pick'])}</sup>" if not pd.isna(row['pick']) else ""
                    st.write(row['player_name'])
                with prob_col:
                    prob = f"{row['prob']:.1f}%"
                    st.write(prob)

with tab_xp:
    st.info("Page under construction...")
    xp = odds_and_picks.groupby("player_name")["prob"].sum().sort_values(ascending=False).reset_index()
    xp = xp[xp["player_name"] != "--"]
    xp["prob"] = (xp["prob"] / 100).round(2)

    for _, row in xp.iterrows():
        #Horizontal metric display
        st.metric(label=row["player_name"], value=f"{row['prob']:.2f}")