import streamlit as st


def render_xpoints_tab(players):

    merged = st.session_state["merged"].copy()

    merged["points"] = merged["prob"] * merged["resolved"] / 100

    xp = merged.groupby(["player_name"])[["prob", "points", "prob_delta"]].sum().sort_values(["points", "prob"], ascending=False).reset_index()
    xp = xp[xp["player_name"].isin(players)].reset_index(drop=True)
    xp["prob"] = xp["prob"] / 100
    xp["prob_delta"] = xp["prob_delta"] / 100

    cols = st.columns(len(players), border=False)
    for i, row in xp.iterrows():
        with cols[i]:
            st.metric(label=f"{i+1}. **{row['player_name']}**", value=row['prob'], delta=row['prob_delta'] if abs(row['prob_delta']) >= 0.01/2 else None, format="%.2f")
            n_wins = int(row["points"])
            if n_wins > 0:
                with st.expander(f"Wins: {n_wins}", type="compact"):
                    wins = merged.copy()[(merged["player_name"] == row["player_name"]) & (merged["prob"] > 90)].sort_values("league")
                    with st.container(horizontal=True, vertical_alignment="center", gap="xsmall"):
                        for _, win in wins.iterrows():
                            st.write(win['team'])
                            st.caption(win['league'])