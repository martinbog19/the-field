import streamlit as st
import requests
from requests.exceptions import ConnectionError
import pandas as pd

from .name_maps.kalshi import name_map as nm_kalshi
from .name_maps.polymarket import name_map as nm_polymarket



class NotFoundError(Exception):
    pass

def get_kalshi_data(event_ticker: str):

    if pd.isna(event_ticker):
        raise NotFoundError(f"No markets available for event ticker: {event_ticker}")

    event_ticker = event_ticker.upper().strip()
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker={event_ticker}"
    try:
        response = requests.get(url)
    except ConnectionError:
        st.error("No connection")
        st.stop()

    markets = response.json()["markets"]
    if len(markets) == 0:
        raise NotFoundError(f"No markets found for event ticker: {event_ticker}")

    teams, probs, tickers = [], [], []
    for market in markets:

        team = market["yes_sub_title"].strip()
        teams.append(team)

        ask_price = float(market["yes_ask_dollars"])
        bid_price = float(market["yes_bid_dollars"])
        prob = 100 * (ask_price + bid_price) / 2 if (ask_price > 0 and bid_price > 0) else 0
        probs.append(prob)
        tickers.append(market["ticker"])

    df = pd.DataFrame(
        {
            "team": teams,
            "prob": probs,
            "prob_delta": 0, # Not implemented yet
            "market_ticker": tickers,
            "resolved": False, # Not implemented yet
        }
    )
    df["prob"] = 100 * df["prob"] / df["prob"].sum()

    return df


def get_polymarket_data(event_slug: str):

    print(event_slug)

    if pd.isna(event_slug):
        raise NotFoundError(f"No markets available for event slug: {event_slug}")
    
    event_slug = event_slug.lower().strip()
    url = f"https://gamma-api.polymarket.com/events/slug/{event_slug}"
    try:
        response = requests.get(url)
    except ConnectionError:
        st.error("No connection")
        st.stop()

    try:
        markets = response.json()["markets"]
    except (KeyError, ValueError):
        raise NotFoundError(f"Failed to fetch markets for event slug: {event_slug}")

    teams, probs, prob_deltas, slugs, resolved = [], [], [], [], []
    for market in markets:

        team = market["groupItemTitle"].strip()
        if team.startswith("Team ") or team.startswith("Player ") or team == "Other":
            continue
        teams.append(team)

        ask_price = float(market.get("bestAsk", 0.0))
        bid_price = float(market.get("bestBid", 0.0))
        prob = (ask_price + bid_price) / 2 if (ask_price > 0 and bid_price > 0) else 0
        # # prob = float(market["outcomePrices"][0])
        # prob = float(market["outcomePrices"].lstrip("[").split(",")[0].strip('"'))
        probs.append(prob)
        prob_delta = float(market.get("oneWeekPriceChange", 0.0))
        prob_deltas.append(prob_delta)
        slugs.append(market["slug"])
        resolved.append(market.get("umaResolutionStatus", "") == "resolved")

    df = pd.DataFrame(
        {
            "team": teams,
            "prob": probs,
            "event_slug": slugs,
            "resolved": resolved,
        }
    )
    prob_sum = df["prob"].sum()
    df["prob"] = 100 * df["prob"] / prob_sum
    df["prob_delta"] = 100 * pd.Series(prob_deltas) / prob_sum

    return df


def fetch_odds_data(leagues: pd.DataFrame, odds_provider: str):

    with st.spinner(f"Fetching {odds_provider} odds...", show_time=True):

        fetch_fn = get_polymarket_data if odds_provider == "Polymarket" else get_kalshi_data
        market_id_col = "polymarket_slug" if odds_provider == "Polymarket" else "kalshi_ticker"
        name_map = nm_polymarket if odds_provider == "Polymarket" else nm_kalshi

        odds, not_found_leagues = [], []
        for _, league in leagues.iterrows():

            try:
                df = fetch_fn(league[market_id_col]).sort_values(by="prob", ascending=False)
                df["league"] = league["league_name"]
                df["team"] = df["team"].apply(lambda x: name_map.get(league["league_name"], {}).get(x, x))
            except NotFoundError as e:
                not_found_leagues.append(league["league_name"])
                continue
            odds.append(df)


        if odds:
            return pd.concat(odds).reset_index(drop=True), not_found_leagues
        else:
            return pd.DataFrame(columns=["team", "league", "prob", "prob_delta", "resolved"]), not_found_leagues





def _american_odds_to_pct(odds: str):
    odds = float(odds)
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return -odds / (-odds + 100)


def get_espn_data(endpoint: str, team_ids: pd.DataFrame):

    endpoint = endpoint.lower().strip()
    url = "https://sports.core.api.espn.com/v2/" + endpoint
    response = requests.get(url)

    data = [x for x in response.json()["items"] if x.get("name", "") == "NCAA(B) - Winner"][0]
    markets = data["futures"][0]["books"]

    ids, probs = [], []
    for market in markets:

        odds = market["value"]
        prob = _american_odds_to_pct(odds)
        if prob < 0.01:
            continue
        probs.append(prob)

        url_tm = market["team"]["$ref"]
        rhs = url_tm.split("/")[-1]
        team_id = rhs.split("?")[0] if "?" in rhs else rhs
        ids.append(team_id)

    df = pd.DataFrame(
        {
            "team_id": ids,
            "prob": probs,
        }
    )
    df["team_id"] = df["team_id"].astype(int)
    df = df.merge(team_ids, on="team_id", how="left")
    df["prob_delta"] = 0  # Not implemented yet
    df["resolved"] = False  # Not implemented yet

    prob_sum = df["prob"].sum()
    df["prob"] = 100 * df["prob"] / prob_sum

    return df