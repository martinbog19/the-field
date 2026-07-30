import pandas as pd
import streamlit as st

from ..utils import prob2hex


def render_draft_tab(players, leagues, is_mobile):

    if is_mobile:
        settings = [st.expander(filt, expanded=False, type="compact", key=f"draft_exp_{filt}") for filt in ["Players", "Leagues"]]
    else:
        with st.expander("Filters", expanded=False, type="compact", key="draft_exp_filters"):
            settings = st.columns([2, 5], gap="medium", vertical_alignment="top")

    with settings[0]:
        selected_players = st.pills("Players", players, key="draft_players_pills", selection_mode="multi", width="stretch")
        selected_players = selected_players if selected_players else players

    with settings[1]:
        selected_leagues = st.pills("Leagues", sorted(leagues["league_name"].tolist()), key="draft_leagues_pills", selection_mode="multi")
        selected_leagues = selected_leagues if selected_leagues else sorted(leagues["league_name"].tolist())

    merged = st.session_state["merged"].copy()

    display_draft = merged[
        merged["player_name"].isin(selected_players)
        & merged["league"].isin(selected_leagues)
    ]

    display_draft = display_draft[["pick", "round", "player_name", "team", "league", "prob"]].sort_values("pick").reset_index(drop=True)
    display_draft = display_draft.rename(columns={"player_name": "player", "team": "selection", "prob": "live_probability"})
    display_draft["live_probability"] = display_draft["live_probability"].apply(lambda x: f"{x:.1f}" if not pd.isna(x) else "")
    display_draft.columns = [x.capitalize().replace("_", " ") for x in display_draft.columns]
    display_draft = display_draft.rename(columns={"Live probability": "Live probability (%)"})
    display_draft["Pick"] = display_draft["Pick"].astype(int)
    display_draft["Round"] = display_draft["Round"].astype(int)

    display_draft_styled = display_draft.style
    display_draft_styled = display_draft_styled.map(lambda x: "color: #15eb80" if x == "The field" else "color: white", subset=["Selection"])
    display_draft_styled = display_draft_styled.map(prob2hex, subset=["Live probability (%)"])

    st.dataframe(display_draft_styled, hide_index=True)