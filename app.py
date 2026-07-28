import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import os

from src.api import get_kalshi_data, get_polymarket_data, get_espn_data, NotFoundError

from utils.map.kalshi import name_map as nm_kalshi
from utils.map.polymarket import name_map as nm_polymarket

from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="The field", page_icon="🏈", layout="wide")

st.title("The field: Live tracking")

st.warning("🚧 Page under construction...")

screen_width = streamlit_js_eval(js_expressions="screen.width", key="SCR")
st.write(f"Screen width is {screen_width}")
is_mobile = True#screen_width is not None and screen_width < 640

players = ["Krish", "Lucas", "Martin", "Thomas", "Tommy"]


leagues = pd.read_csv("data/leagues.csv").sort_values("end_date").reset_index(drop=True)
draft = pd.read_csv("data/Sports Draft - Draft.csv").sort_values("pick").reset_index(drop=True)

with st.container(horizontal=True, vertical_alignment="bottom"):
    odds_provider = st.pills("Odds source", ["Polymarket", "Kalshi"], default=st.session_state.get("odds_provider", "Polymarket"), required=True, disabled=True)
    last_refreshed = st.session_state.get("last_refreshed")
    last_refreshed_msg = f"(last refreshed: {last_refreshed})" if last_refreshed else ""
    st.button("↻ Refresh", type="tertiary", help=f"Refresh {odds_provider} data {last_refreshed_msg}", on_click=lambda: st.session_state.clear())

fetch_fn = get_polymarket_data if odds_provider == "Polymarket" else get_kalshi_data
market_id_col = "polymarket_slug" if odds_provider == "Polymarket" else "kalshi_ticker"
name_map = nm_polymarket if odds_provider == "Polymarket" else nm_kalshi

tab_main, tab_xp, tab_draft = st.tabs(["Live odds", "xPoints", "Draft"])

with tab_main:
    if is_mobile:
        settings = [st.expander(filt, expanded=False, type="compact", key=f"exp_{filt}") for filt in ["Players", "Leagues"]]
    else:
        settings = st.columns([2, 5], gap="medium", vertical_alignment="top")
    columns = st.columns(3)

with settings[0]:
    selected_players = st.pills("Players", players, key="players_pills", selection_mode="multi", width="stretch")
    hide_unpicked = st.toggle("Hide unpicked teams/players", value=True)

with settings[1]:
    selected_leagues = st.pills("Leagues", sorted(leagues["league_name"].tolist()), key="leagues_pills", selection_mode="multi")

if "odds_and_picks" not in st.session_state or st.session_state.get("odds_provider") != odds_provider:
    st.session_state["odds_provider"] = odds_provider
    with st.spinner(f"Fetching {odds_provider} odds..."):
        odds, not_found_leagues = [], []
        for i, league in leagues.iterrows():

            if league["league_name"] not in selected_leagues and len(selected_leagues) > 0:
                continue

            use_espn = pd.notna(league["espn_endpoint"])
            fetch_fn_used = get_espn_data if use_espn else fetch_fn
            market_id_col_used = "espn_endpoint" if use_espn else market_id_col
            team_ids = pd.read_csv("data/march_madness_espn_team_ids.csv") if use_espn else None

            try:
                df = fetch_fn_used(league[market_id_col_used], team_ids=team_ids).sort_values(by="prob", ascending=False)
                # df = df[df["prob"] > 0]
                df["league"] = league["league_name"]
                df["team"] = df["team"].apply(lambda x: name_map.get(league["league_name"], {}).get(x, x))
            except NotFoundError as e:
                not_found_leagues.append(league["league_name"])
                continue
            odds.append(df)

        odds = pd.concat(odds).reset_index(drop=True) if odds else pd.DataFrame(columns=["team", "league", "prob", "prob_delta", "resolved"])
        merged = odds.merge(draft, on=["team", "league"], how="outer")
        merged["player_name"] = merged["player_name"].fillna("--")
        merged["prob"] = merged["prob"].fillna(0.)

        not_found_picks_idx = merged[merged["league"].isin(not_found_leagues)].index.tolist()
        merged.loc[not_found_picks_idx, "prob"] = None

        st.session_state["odds_and_picks"] = merged
        st.session_state["last_refreshed"] = datetime.now().strftime("%H:%M:%S")

count = 0
odds_and_picks = st.session_state["odds_and_picks"]
for i, league in leagues.iterrows():

    league_name = league["league_name"]

    if league_name not in selected_leagues and len(selected_leagues) > 0:
        continue

    picks = odds_and_picks.copy()[odds_and_picks["league"] == league_name].reset_index(drop=True)
    valid_league = picks["prob"].notna().sum() > 0
    if valid_league:
        field_prob = 100 - picks[picks["player_name"] != "--"]["prob"].sum()
        field_prob_delta = picks[picks["player_name"] == "--"]["prob_delta"].sum()
        field_idx = picks.query("team == 'The field'").index[0]
        picks.at[field_idx, "prob"] = field_prob
        picks.at[field_idx, "prob_delta"] = field_prob_delta

    picks = picks.sort_values(["prob", "pick"], ascending=[False, True])

    with columns[count % 3]:

        container = st.container(height="stretch" if is_mobile else 500, gap="xxsmall")
        with container:

            logo_path = f"assets/logos/{league_name.lower().replace(' ', '_')}.png"
            if is_mobile:
                if count > 0:
                    st.divider()
                with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
                    with st.container():
                        st.write(f"**{league['league_name']}**")
                        st.caption(datetime.strftime(datetime.strptime(league["end_date"], "%Y-%m-%d"), "%B %Y"))
                    if os.path.exists(logo_path):
                        st.image(logo_path, width=48)
            else:
                c1, c2 = st.columns([3, 1])
                if os.path.exists(logo_path):
                    c2.image(logo_path, width="stretch")
                c1.write(f"**{league['league_name']}**")
                c1.caption(datetime.strftime(datetime.strptime(league["end_date"], "%Y-%m-%d"), "%B %Y"))
            if not valid_league:
                st.warning(f"No {odds_provider} odds available for this league.")
                st.space("xsmall")
            else:
                st.space("small")

            if picks.empty:
                st.warning(f"No {odds_provider} odds found for this league.")
                continue

            if selected_players:
                picks = picks[picks["player_name"].isin(selected_players)]
            if hide_unpicked:
                picks = picks[picks["player_name"] != "--"]

            if not is_mobile:
                tm_col, pick_col, prob_col = st.columns([6, 2, 2])
            for _, row in picks.iterrows():
                team_color = "#15eb80" if row["team"] == "The field" else "white"
                prob = f"{row['prob']:.1f}%" if not pd.isna(row['prob']) else "--"
                if row['prob_delta'] >= 0.5:
                    arrow, delta_color = "▲", "#15eb80"
                elif row['prob_delta'] <= -0.5:
                    arrow, delta_color = "▼", "#fc0362"
                else:
                    arrow, delta_color = "--" if not is_mobile else "", "#424242"
                if is_mobile:
                    # Built as a single flex row (not st.columns) so team/pick/prob stay
                    # aligned on one line instead of stacking on narrow viewports.
                    st.markdown(
                        f"""<div style='display:flex;align-items:center;gap:8px;padding:2px 0;'>
                        <span style='flex:3;min-width:0;color:{team_color};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{row['team']}</span>
                        <span style='flex:1;text-align:right;white-space:nowrap;'>{row['player_name']}</span>
                        <span style='flex:1;text-align:right;white-space:nowrap;'><span style='color:{delta_color}'>{arrow}</span> {prob}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    with tm_col:
                        st.markdown(f"<span style='color:{team_color}'>{row['team']}</span>", unsafe_allow_html=True)
                    with pick_col:
                        st.write(row['player_name'])
                    with prob_col:
                        st.markdown(f"<span style='color:{delta_color}'>{arrow}</span> {prob}", unsafe_allow_html=True)
    count += 1

with tab_xp:

    points = odds_and_picks.copy()
    points["points"] = points["prob"] / 100 * points["resolved"]

    xp = points.groupby("player_name")[["prob", "points", "prob_delta"]].sum().sort_values(["points", "prob"], ascending=False).reset_index()
    xp = xp[xp["player_name"].isin(players)].reset_index(drop=True)
    xp["prob"] = xp["prob"] / 100
    xp["prob_delta"] = xp["prob_delta"] / 100

    cols = st.columns(len(players), border=False)
    for i, row in xp.iterrows():
        with cols[i]:
            # with st.container(horizontal=True, vertical_alignment="bottom"):
            st.metric(label=f"{i+1}. **{row['player_name']}**", value=row['prob'], delta=row['prob_delta'] if abs(row['prob_delta']) >= 0.01/2 else None, format="%.2f")
            n_wins = int(row["points"])
            if n_wins > 0:
                with st.expander(f"Wins: {n_wins}", type="compact"):
                    wins = points.copy()[(points["player_name"] == row["player_name"]) & (points["prob"] > 90)].sort_values("league")
                    with st.container(horizontal=True, vertical_alignment="center", gap="xsmall"):
                        for _, win in wins.iterrows():
                            st.write(win['team'])
                            st.caption(win['league'])


    #     #Horizontal metric display
    #     st.metric(label=row["player_name"], value=f"{row['prob']:.2f}")


with tab_draft:

    def _color_prob(val: float, target_hex="#15eb80"):

        if (isinstance(val, str) and not val) or pd.isna(val):
            return "color: white"

        ratio = float(val) / 50 if float(val) <= 50 else 1
        target_hex = target_hex.lstrip('#')
        tr, tg, tb = int(target_hex[0:2], 16), int(target_hex[2:4], 16), int(target_hex[4:6], 16)

        # Interpolate from white (255,255,255) to target
        r = round(255 + (tr - 255) * ratio)
        g = round(255 + (tg - 255) * ratio)
        b = round(255 + (tb - 255) * ratio)

        return f'color: #{r:02x}{g:02x}{b:02x}'

    display_draft = odds_and_picks.copy()[odds_and_picks["player_name"].isin(players)]
    display_draft = display_draft[["pick", "round", "player_name", "team", "league", "prob"]].sort_values("pick").reset_index(drop=True)
    display_draft = display_draft.rename(columns={"player_name": "player", "team": "selection", "prob": "live_probability"})
    display_draft["live_probability"] = display_draft["live_probability"].apply(lambda x: f"{x:.1f}" if not pd.isna(x) else "")
    display_draft.columns = [x.capitalize().replace("_", " ") for x in display_draft.columns]
    display_draft = display_draft.rename(columns={"Live probability": "Live probability (%)"})
    display_draft["Pick"] = display_draft["Pick"].astype(int)#.apply(lambda x: f"{int(x)}")
    display_draft["Round"] = display_draft["Round"].astype(int)

    display_draft_styled = display_draft.style.map(_color_prob, subset=["Live probability (%)"])

    st.dataframe(display_draft_styled, hide_index=True, width=screen_width)


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