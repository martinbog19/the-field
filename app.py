import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

from src.api import get_kalshi_data, get_polymarket_data, NotFoundError

from utils.map.kalshi import name_map as nm_kalshi
from utils.map.polymarket import name_map as nm_polymarket

st.set_page_config(page_title="The field", page_icon="🏈", layout="wide")

st.title("The field: Live tracking")

tab_main, tab_xp = st.tabs(["Live odds", "xPoints"])

with tab_main:
    st.info("🚧 Page under construction...")
    settings = st.columns([2, 4, 5, 2])
    columns = st.columns(3)

leagues = pd.read_csv("data/leagues.csv").sort_values("end_date").reset_index(drop=True)
draft = pd.read_csv("data/Sports Draft - Draft.csv").sort_values("pick").reset_index(drop=True)

with settings[0]:
    odds_provider = st.pills("Odds source", ["Kalshi", "Polymarket"], default="Kalshi", required=True, key="odds_pills", help="Kalshi/Polymarket merge in development...")
    fetch_fn = get_polymarket_data if odds_provider == "Polymarket" else get_kalshi_data
    market_id_col = "polymarket_slug" if odds_provider == "Polymarket" else "kalshi_ticker"
    name_map = nm_polymarket if odds_provider == "Polymarket" else nm_kalshi

with settings[1]:
    selected_players = st.pills("Players", ["Krish", "Lucas", "Martin", "Thomas", "Tommy"], key="players_pills", selection_mode="multi")

with settings[2]:
    selected_leagues = st.pills("Leagues", sorted(leagues["league_name"].tolist()), key="leagues_pills", selection_mode="multi")

with settings[3]:
    hide_unpicked = st.toggle("Hide unpicked teams/players", value=True)

with st.spinner(f"Fetching {odds_provider} odds..."):
    odds, not_found_leagues = [], []
    for i, league in leagues.iterrows():

        if league["league_name"] not in selected_leagues and len(selected_leagues) > 0:
            continue

        try:
            df = fetch_fn(league[market_id_col]).sort_values(by="prob", ascending=False)
            df = df[df["prob"] > 0]
            df["league"] = league["league_name"]
            df["team"] = df["team"].apply(lambda x: name_map.get(league["league_name"], {}).get(x, x))
        except NotFoundError as e:
            not_found_leagues.append(league["league_name"])
            continue
        odds.append(df)

    odds = pd.concat(odds).reset_index(drop=True) if odds else pd.DataFrame()
    odds_and_picks = odds.merge(draft, on=["team", "league"], how="outer")
    odds_and_picks["player_name"] = odds_and_picks["player_name"].fillna("--")
    odds_and_picks["prob"] = odds_and_picks["prob"].fillna(0.)

    not_found_picks_idx = odds_and_picks[odds_and_picks["league"].isin(not_found_leagues)].index.tolist()
    odds_and_picks.loc[not_found_picks_idx, "prob"] = None

count = 0
for i, league in leagues.iterrows():

    if league["league_name"] not in selected_leagues and len(selected_leagues) > 0:
        continue

    picks = odds_and_picks.copy()[odds_and_picks["league"] == league["league_name"]].reset_index(drop=True)
    if league["league_name"] not in not_found_leagues:
        field_odds = 100 - picks[picks["player_name"] != "--"]["prob"].sum()
        field_idx = picks.query("team == 'The field'").index[0]
        picks.at[field_idx, "prob"] = field_odds

    picks = picks.sort_values(["prob", "pick"], ascending=[False, True])

    with columns[count % 3]:

        container = st.container(height=500, gap="xxsmall")
        with container:

            # c1, c2 = st.columns([1, 1])
            st.write(league["league_name"])
            st.caption(datetime.strftime(datetime.strptime(league["end_date"], "%Y-%m-%d"), "%B %Y"))
            # c2.image("PL_Logo_Horizontal_RGB_White_HR.png")
            if league["league_name"] in not_found_leagues:
                st.warning(f"No {odds_provider} odds available for this league.")
                st.space("xsmall")
            else:
                st.space("small")
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
                color = "#15eb80" if row["team"] == "The field" else "white"
                with tm_col:
                    st.markdown(f"<span style='color:{color}'>{row['team']}</span>", unsafe_allow_html=True)
                with pick_col:
                    # pick_str = f" {row['player_name']} <sup>#{int(row['pick'])}</sup>" if not pd.isna(row['pick']) else "--"
                    # pick_str = f"<sup>#{int(row['pick'])}</sup>" if not pd.isna(row['pick']) else ""
                    st.write(row['player_name'])
                with prob_col:
                    prob = f"{row['prob']:.1f}%" if not pd.isna(row['prob']) else "--"
                    st.write(prob)
    count += 1


with tab_xp:
    st.info("🚧 Page under construction...")
    xp = odds_and_picks.groupby("player_name")["prob"].sum().sort_values(ascending=False).reset_index()
    xp = xp[xp["player_name"] != "--"]
    xp["prob"] = (xp["prob"] / 100).round(2)

    for _, row in xp.iterrows():
        #Horizontal metric display
        st.metric(label=row["player_name"], value=f"{row['prob']:.2f}")


# st.divider()

# st.dataframe(odds_and_picks.sort_values("prob").iloc[-1])



# import requests

# ticker = odds_and_picks.sort_values("prob").iloc[-1]["market_ticker"]
# series_ticker = ticker.split("-")[0]
# time_now = int(time.time())
# time_last_month = int(time.time()) - 30 * 24 * 60 * 60
# st.write(time_now)
    

# url = f"https://external-api.kalshi.com/trade-api/v2/series/{series_ticker}/markets/{ticker}/candlesticks"

# response = requests.get(
#     url,
#     params={
#         "start_ts": time_last_month,
#         "end_ts": time_now,
#         "period_interval": 1440,
#     }
# )

# trend = pd.DataFrame(response.json()["candlesticks"]).sort_values("end_period_ts")
# trend["time"] = (trend["end_period_ts"].astype(float) - time_last_month) / (60 * 60 * 24)
# trend["price"] = trend["price"].apply(lambda x: float(x["mean_dollars"]))
# st.dataframe(trend)


# st.line_chart(trend, x="time", y="price", color="#15eb80")

# st.popover("Label")