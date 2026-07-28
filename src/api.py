import requests
import pandas as pd

class NotFoundError(Exception):
    pass

def get_kalshi_data(event_ticker: str, team_ids = None):

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


def get_polymarket_data(event_slug: str, team_ids = None):
    
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