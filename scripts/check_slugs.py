import sys

import pandas as pd

from src.api import NotFoundError, get_kalshi_data, get_polymarket_data


def main():
    leagues = pd.read_csv("data/leagues.csv")
    failures = []

    for _, league in leagues.iterrows():
        name = league["league_name"]

        if not pd.isna(league["polymarket_slug"]):
            try:
                get_polymarket_data(league["polymarket_slug"])
            except NotFoundError as e:
                failures.append(f"[Polymarket] {name} ({league['polymarket_slug']}): {e}")

        if not pd.isna(league["kalshi_ticker"]):
            try:
                get_kalshi_data(league["kalshi_ticker"])
            except NotFoundError as e:
                failures.append(f"[Kalshi] {name} ({league['kalshi_ticker']}): {e}")

    if failures:
        print("Broken league identifiers found:")
        for f in failures:
            print(f" - {f}")
        sys.exit(1)

    print(f"OK: all provider identifiers resolved for {len(leagues)}.")


if __name__ == "__main__":
    main()
