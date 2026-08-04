import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime

from ..utils import prob2hex


@st.cache_data
def _arrow_img_tag(delta):
    if pd.isna(delta) or abs(delta) <= 0.5:
        return ""
    count = 3 if abs(delta) >= 5 else 2 if abs(delta) >= 2 else 1
    direction = "up" if delta > 0 else "down"
    path = f"assets/arrows/{direction}_{count}.png"
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return f"<img src='data:image/png;base64,{encoded}' style='width:12px;vertical-align:middle;'/>"


def render_main_tab(players, leagues, is_mobile):

    merged = st.session_state["merged"].copy()
    odds_provider = st.session_state["odds_provider"]

    if is_mobile:
        settings = [st.expander(filt, expanded=False, type="compact", key=f"exp_{filt}") for filt in ["Players", "Leagues"]]
    else:
        settings = st.columns([2, 5], gap="medium", vertical_alignment="top")

    with settings[0]:
        selected_players = st.pills("Players", players, key="players_pills", selection_mode="multi", width="stretch")
        if len(selected_players) == 0:
            hide_unpicked = st.toggle("Hide unpicked teams/players", value=True, key="hide_unpicked")
        else:
            hide_unpicked = st.toggle("Hide unpicked teams/players", value=True, key="hide_unpicked_dummy", disabled=True)
        selected_players = selected_players if selected_players else players

    with settings[1]:
        selected_leagues = st.pills("Leagues", sorted(leagues["league_name"].tolist()), key="leagues_pills", selection_mode="multi")
        selected_leagues = selected_leagues if selected_leagues else sorted(leagues["league_name"].tolist())

    merged = merged.copy()[
        (merged["league"].isin(selected_leagues))
        & (
            (merged["player_name"].isin(selected_players))
            | ((not hide_unpicked) & (merged["player_name"] == "--"))
        )
    ]

    columns = st.columns(3 if not is_mobile else 1, gap="medium", vertical_alignment="top")
    leagues_iterator = leagues.copy()[leagues["league_name"].isin(selected_leagues)].sort_values("end_date").reset_index(drop=True)
    for i, league in leagues_iterator.iterrows():

        league_name = league["league_name"]
        logo_path = f"assets/logos/{league_name.lower().replace(' ', '_')}.png"

        picks = merged.copy()[merged["league"] == league_name].reset_index(drop=True)
        picks = picks.sort_values(["prob", "pick"], ascending=[False, True])

        with columns[i % 3 if not is_mobile else 0]:

            container = st.container(height="stretch" if is_mobile else 400, gap="xxsmall")
            with container:

                if is_mobile:
                    if i > 0:
                        st.divider()

                    with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
                        with st.container():
                            st.write(f"**{league['league_name']}**")
                            st.caption(datetime.strftime(datetime.strptime(league["end_date"], "%Y-%m-%d"), "%B %Y"))
                        if os.path.exists(logo_path):
                            st.image(logo_path, width=48)
                else:
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{league['league_name']}**")
                    c1.caption(datetime.strftime(datetime.strptime(league["end_date"], "%Y-%m-%d"), "%B %Y"))
                    if os.path.exists(logo_path):
                        c2.image(logo_path, width=96)

                if picks["prob"].isna().all():
                    st.warning(f"No {odds_provider} odds yet available.")
                    st.space("xsmall")
                else:
                    st.space("small")

                for _, pick in picks.iterrows():
                    accent_color = "#15eb80" if pick["team"] == "The field" else "white"
                    prob_color = prob2hex(pick["prob"])
                    prob = f"{pick['prob']:.1f}%" if not pd.isna(pick['prob']) else "--"
                        
                    arrow = _arrow_img_tag(pick["prob_delta"])

                    st.markdown(
                        f"""<div style='display:flex;align-items:center;gap:36px;padding:6px 0;'>
                        <span style='flex:3;min-width:0;color:{accent_color};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{pick['team']}</span>
                        <span style='flex:1;text-align:left;white-space:nowrap;'>{pick['player_name']}</span>
                        <span style='flex:1;display:inline-flex;align-items:center;justify-content:flex-end;gap:6px;white-space:nowrap;'>{arrow}<span style='{prob_color}'>{prob}</span></span>
                        </div>""",
                        unsafe_allow_html=True,
                    )