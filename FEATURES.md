# FEATURES

Request a new feature by adding a line below!

## Ideas

- [ ] **Price history / trend chart.** `get_kalshi_data` returns a `market_ticker`, and there's already a working (commented-out) Kalshi candlestick-fetch at the bottom of `app.py`. Revive it as an expander/popover on each pick showing a probability-over-time line chart (`st.line_chart`).
- [ ] **Season-long standings chart.** Right now xPoints only shows the *current* snapshot. Snapshot `merged` to disk once a day (e.g. GitHub Action calling a small script, or on first load of the day) and chart each player's expected points over the season instead of just the live number.
- [ ] **"Biggest movers" summary.** `prob_delta` is already computed per team — surface a top-level list of the largest movers across all leagues (good/bad for you) instead of only showing arrows inline per row.
- [ ] **Wire up ESPN as a third provider.** `get_espn_data` + `data/march_madness_espn_team_ids.csv` exist but nothing calls them — March Madness has no live provider until the bracket exists on Kalshi/Polymarket. Either finish this path or drop the dead code.
- [ ] **Auto-refresh on a timer.** Currently odds only update on manual click or provider switch. `st.fragment(run_every=...)` around the fetch would let it refresh itself every few minutes without a full rerun.
- [ ] **Player detail view.** A page/expander per player showing their full portfolio ranked by live probability, across leagues — useful once you're eyeballing 175 picks across 15 leagues.
- [ ] **Resolved-market banner.** When a pick actually wins (market resolves), toast/notify rather than requiring someone to notice the xPoints tab changed.
- [ ] **Missing league logos.** Only 2 of 15 leagues (`abu_dhabi_grand_prix`, `premier_league`) have a logo in `assets/logos/`; the rest silently skip the image. Fill in the rest.

## Known bugs / tech debt

- [ ] **xPoints correctness.** `resolved` is hardcoded `False` for Kalshi (`api.py`), so switching providers zeroes win counts. `n_wins = int(row["points"])` truncates and should be `round()`. The win-count expander in `xpoints.py` filters on `prob > 90` while the count above it uses `resolved` — these two can disagree.
- [ ] **`hide_unpicked` toggle loses state.** In `app.py`, the toggle is rendered under a different key (`hide_unpicked` vs `hide_unpicked_dummy`) depending on whether players are selected. Streamlit drops session state for a key that isn't rendered in a run, so the user's choice silently resets. Fix: one stable key, `disabled=bool(selected_players)`.
- [ ] **Silent name-map mismatches.** A drafted team not matched to a provider's team name (via `src/name_maps/*`) currently either goes to 0% or gets folded into "The field" with no warning. Worth surfacing a debug banner listing any drafted team that fetched successfully but didn't match.
- [ ] **Division by zero when a league has no live prices.** `prob_sum` in `api.py` can be 0 pre-market or post-resolution, producing `inf` deltas.
- [ ] **Pin `requirements.txt`.** Only `streamlit_js_eval` is listed; `streamlit`/`pandas`/`requests` are unpinned transitive deps, and the app leans on very recent Streamlit APIs (`st.pills`, `st.space`, `height="stretch"`). A Streamlit upgrade could break the deployed app with no local warning.
- [ ] **No caching.** `fetch_odds_data` fires ~15 serial HTTP requests per session with no `@st.cache_data`, and the CSVs in `app.py` reload on every widget interaction.
- [ ] **No tests.** `merge_draft_odds`, `prob2hex`, and the odds-normalization functions in `api.py` are pure DataFrame functions — cheap to test, and exactly the code most likely to silently break.

## Refactors

- [ ] **`render_main_tab()`.** Pull the "Live odds" tab body out of `app.py` into `src/tabs/main.py`, matching `render_draft_tab` / `render_xpoints_tab`.
- [ ] **Shared filter widget.** The players/leagues pills + mobile-expander-vs-column logic is duplicated between `app.py` and `draft.py`. Extract to one `render_filters(prefix, players, leagues, is_mobile)`.
- [ ] **Pass `merged` explicitly.** `draft.py` and `xpoints.py` both reach into `st.session_state["merged"]` directly instead of taking it as a parameter — makes the tab functions harder to test in isolation.
