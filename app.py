import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

from src.tabs.draft import render_draft_tab
from src.tabs.xpoints import render_xpoints_tab
from src.tabs.main import render_main_tab
from src.transform import merge_draft_odds


st.set_page_config(page_title="The field", page_icon="🏈", layout="wide")
screen_width = streamlit_js_eval(js_expressions="screen.width", key="SCR")

title_col, dd_col = st.columns([3, 1])
with title_col:
    st.title("The field: Live tracking")
with dd_col:
    room = st.selectbox("Select room:", ["Martin's friends", "Krish's friends"], index=["martin", "krish"].index(st.query_params.get("room_id", "martin")))
    room_id = "martin" if room == "Martin's friends" else "krish"

is_mobile = screen_width is not None and screen_width < 640
is_mobile = True


with open(f"data/{room_id}/leagues.txt", "r") as f:
    room_leagues = f.read().splitlines()
leagues = pd.read_csv(f"data/leagues.csv")
leagues = leagues[leagues["league_name"].isin(room_leagues)]
draft = pd.read_csv(f"data/{room_id}/draft.csv").sort_values("pick").reset_index(drop=True)
players = sorted(draft["player_name"].unique().tolist())

odds_refresh_container = st.container(horizontal=True, vertical_alignment="bottom")
with odds_refresh_container:
    odds_provider = st.pills("Odds source", ["Polymarket", "Kalshi"], default=st.session_state.get("odds_provider", "Polymarket"), required=True, disabled=False)
    if st.button("↻ Refresh", key="refresh_odds", type="tertiary", help=f"Refresh {odds_provider} data"):
        st.session_state.pop("merged", None)

if (
    "merged" not in st.session_state
    or st.session_state.get("odds_provider") != odds_provider
    or st.session_state.get("room_id") != room_id
):
    with odds_refresh_container:
        st.session_state["merged"] = merge_draft_odds(draft, leagues, odds_provider)
        if "last_refreshed" in st.session_state:
            st.toast(f"Successfully pulled {odds_provider} data!", duration=3)
        st.session_state["last_refreshed"] = datetime.now()
        st.session_state["odds_provider"] = odds_provider
        st.session_state["room_id"] = room_id


merged = st.session_state["merged"].copy()


tab_main, tab_xp, tab_draft, tab_trends = st.tabs(["Live odds", "xPoints", "Draft", "Trends"])

with tab_main:
    render_main_tab(players, leagues, is_mobile)

with tab_xp:
    render_xpoints_tab(players)

with tab_draft:
    render_draft_tab(players, leagues, is_mobile)


with tab_trends:

    if st.session_state.get("odds_provider") != "Polymarket":
        st.warning("Trends are only available for Polymarket data.", icon="⚠️")
        st.stop()
    else:
        st.warning("Page in development...", icon="⚠️")

    merged = st.session_state["merged"].copy().sort_values("prob_delta", ascending=False)
    merged = merged[merged["prob_delta"].notna() & (merged["player_name"].isin(players))]

    hot = merged.head(3)
    cold = merged.tail(3).iloc[::-1]

    col_hot, col_cold, _ = st.columns([1, 1, 2], gap="medium", vertical_alignment="top")
    with col_hot:
        st.write("### 🔥 Hot picks")
        for _, pick in hot.iterrows():
            prob = f"{pick['prob']:.1f}%" if not pd.isna(pick['prob']) else "--"
            st.metric(label=f"{pick['player_name']}: **{pick['team']}** ({pick['league']})", value=prob, delta=f"{pick['prob_delta']:+.1f}%")
    with col_cold:
        st.write("### ❄️ Cold picks")
        for _, pick in cold.iterrows():
            prob = f"{pick['prob']:.1f}%" if not pd.isna(pick['prob']) else "--"
            st.metric(label=f"{pick['player_name']}: **{pick['team']}** ({pick['league']})", value=prob, delta=f"{pick['prob_delta']:+.1f}%")