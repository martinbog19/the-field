import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

from src.tabs.draft import render_draft_tab
from src.tabs.xpoints import render_xpoints_tab
from src.transform import merge_draft_odds
from src.utils import prob2hex


st.set_page_config(page_title="The field", page_icon="🏈", layout="wide")
st.title("The field: Live tracking")

screen_width = streamlit_js_eval(js_expressions="screen.width", key="SCR")
is_mobile = screen_width is not None and screen_width < 640
device = "mobile" if is_mobile else "desktop"

leagues = pd.read_csv("data/leagues.csv").sort_values("end_date").reset_index(drop=True)
draft = pd.read_csv("data/Sports Draft - Draft.csv").sort_values("pick").reset_index(drop=True)
players = sorted(draft["player_name"].unique().tolist())

odds_refresh_container = st.container(horizontal=True, vertical_alignment="bottom")
with odds_refresh_container:
    odds_provider = st.pills("Odds source", ["Polymarket", "Kalshi"], default=st.session_state.get("odds_provider", "Polymarket"), required=True, disabled=False)
    if st.button("↻ Refresh", key="refresh_odds", type="tertiary", help=f"Refresh {odds_provider} data"):
        st.session_state.pop("merged", None)

if "merged" not in st.session_state or st.session_state.get("odds_provider") != odds_provider:
    with odds_refresh_container:
        st.session_state["merged"] = merge_draft_odds(draft, leagues, odds_provider)
        if "last_refreshed" in st.session_state:
            st.toast(f"Successfully pulled {odds_provider} data!", duration=3)
        st.session_state["last_refreshed"] = datetime.now()
        st.session_state["odds_provider"] = odds_provider


tab_main, tab_xp, tab_draft = st.tabs(["Live odds", "xPoints", "Draft"])

with tab_main:

    merged = st.session_state["merged"].copy()

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

                if not is_mobile:
                    tm_col, pick_col, prob_col = st.columns([6, 2, 2])

                # st.dataframe(picks)
                for _, pick in picks.iterrows():
                    accent_color = "#15eb80" if pick["team"] == "The field" else "white"
                    prob_color = prob2hex(pick["prob"])
                    prob = f"{pick['prob']:.1f}%" if not pd.isna(pick['prob']) else "--"
                        
                    if pick["prob_delta"] >= 0.5:
                        arrow, delta_color = "▲", "#15eb80"
                    elif pick["prob_delta"] <= -0.5:
                        arrow, delta_color = "▼", "#fc0362"
                    else:
                        arrow, delta_color = "", ""

                    # if is_mobile:
                    #     pass
                    # Built as a single flex row (not st.columns) so team/pick/prob stay
                    # aligned on one line instead of stacking on narrow viewports.
                    # Underline "The field"
                    st.markdown(
                        f"""<div style='display:flex;align-items:center;gap:36px;padding:6px 0;'>
                        <span style='flex:3;min-width:0;color:{accent_color};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{pick['team']}</span>
                        <span style='flex:1;text-align:left;white-space:nowrap;'>{pick['player_name']}</span>
                        <span style='flex:1;text-align:right;white-space:nowrap;'><span style='color:{delta_color}'>{arrow}</span> <span style='{prob_color}'>{prob}</span></span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                    # else:
                    #     with tm_col:
                    #         st.markdown(f"<span style='color:{accent_color}'>{pick['team']}</span>", unsafe_allow_html=True)
                    #     with pick_col:
                    #         st.write(pick['player_name'])
                    #     with prob_col:
                    #         st.markdown(f"<span style='color:{delta_color}'>{arrow}</span> {prob}", unsafe_allow_html=True)

with tab_xp:
    render_xpoints_tab(players)


with tab_draft:
    render_draft_tab(
        players,
        leagues,
        is_mobile
    )






# # import requests

# # ticker = odds_and_picks.sort_values("prob").iloc[-1]["market_ticker"]
# # series_ticker = ticker.split("-")[0]
# # time_now = int(time.time())
# # time_last_month = int(time.time()) - 30 * 24 * 60 * 60
# # st.write(time_now)
    

# # url = f"https://external-api.kalshi.com/trade-api/v2/series/{series_ticker}/markets/{ticker}/candlesticks"

# # response = requests.get(
# #     url,
# #     params={
# #         "start_ts": time_last_month,
# #         "end_ts": time_now,
# #         "period_interval": 1440,
# #     }
# # )

# # trend = pd.DataFrame(response.json()["candlesticks"]).sort_values("end_period_ts")
# # trend["time"] = (trend["end_period_ts"].astype(float) - time_last_month) / (60 * 60 * 24)
# # trend["price"] = trend["price"].apply(lambda x: float(x["mean_dollars"]))
# # st.dataframe(trend)


# # st.line_chart(trend, x="time", y="price", color="#15eb80")

# # st.popover("Label")