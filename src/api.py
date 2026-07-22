import requests
import pandas as pd


def get_kalshi_data(event_ticker):

    event_ticker = event_ticker.upper().strip()
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker={event_ticker}"
    response = requests.get(url)

    try:
        markets = response.json()['markets']
    except (KeyError, ValueError):
        markets = []

    teams, probs = [], []
    for market in markets:

        team = market["yes_sub_title"].strip()
        teams.append(team)

        ask_price = float(market["previous_yes_ask_dollars"])
        bid_price = float(market["previous_yes_bid_dollars"])
        prob = 100 * (ask_price + bid_price) / 2 if (ask_price > 0 and bid_price > 0) else 0
        probs.append(prob)

    df = pd.DataFrame(
        {
            "team": teams,
            "prob": probs
        }
    )
    df["prob"] = 100 * df["prob"] / df["prob"].sum()

    return df


def get_polymarket_data(event_slug):
    
    event_slug = event_slug.lower().strip()
    url = f"https://gamma-api.polymarket.com/events/slug/{event_slug}"
    response = requests.get(url)

    try:
        markets = response.json()['markets']
    except (KeyError, ValueError):
        markets = []

    teams, probs = [], []
    for market in markets:

        team = market["groupItemTitle"].strip()
        teams.append(team)

        ask_price = float(market["bestAsk"])
        bid_price = float(market["bestBid"])
        prob = 100 * (ask_price + bid_price) / 2 if (ask_price > 0 and bid_price > 0) else 0
        probs.append(prob)

    df = pd.DataFrame(
        {
            "team": teams,
            "prob": probs
        }
    )
    df["prob"] = 100 * df["prob"] / df["prob"].sum()

    return df
