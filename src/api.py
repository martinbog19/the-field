import requests
import pandas as pd

class NotFoundError(Exception):
    pass

def get_kalshi_data(event_ticker):

    event_ticker = event_ticker.upper().strip()
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker={event_ticker}"
    response = requests.get(url)

    markets = response.json()["markets"]
    if len(markets) == 0:
        raise NotFoundError(f"No markets found for event ticker: {event_ticker}")

    teams, probs, tickers = [], [], []
    for market in markets:

        team = market["yes_sub_title"].strip()
        teams.append(team)

        ask_price = float(market["previous_yes_ask_dollars"])
        bid_price = float(market["previous_yes_bid_dollars"])
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


def get_polymarket_data(event_slug):
    
    event_slug = event_slug.lower().strip()
    url = f"https://gamma-api.polymarket.com/events/slug/{event_slug}"
    response = requests.get(url)

    try:
        markets = response.json()["markets"]
    except (KeyError, ValueError):
        raise NotFoundError(f"Failed to fetch markets for event slug: {event_slug}")

    teams, probs, prob_deltas, slugs, resolved = [], [], [], [], []
    for market in markets:

        team = market["groupItemTitle"].strip()
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
