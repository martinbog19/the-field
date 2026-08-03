import pandas as pd

from .api import fetch_odds_data



def _compute_field_odds(df: pd.DataFrame) -> pd.DataFrame:

    df = df[df["player_name"] == "--"]
    field_probs = df.groupby("league")[["prob", "prob_delta"]].sum().reset_index()
    field_probs["team"] = "The field"
    field_probs = field_probs.rename(columns={"prob": "field_prob", "prob_delta": "field_prob_delta"})

    return field_probs

def merge_draft_odds(draft: pd.DataFrame, leagues: list[str], odds_provider: str) -> pd.DataFrame:

    odds_raw, not_found_leagues = fetch_odds_data(leagues, odds_provider)

    merged = odds_raw.merge(draft, on=["team", "league"], how="outer", indicator=True)

    # Players/teams listed on Polymarket/Kalshi but not selected in draft
    left_merged = merged["_merge"] == "left_only"
    merged.loc[left_merged, "player_name"] = merged.loc[left_merged, "player_name"].fillna("--")

    # Players/teams selected but not listed on Polymarket/Kalshi
    not_listed = (
        (merged["_merge"] == "right_only")
        & (~merged["league"].isin(not_found_leagues))
        & (merged["team"] != "The field")
    )
    merged.loc[not_listed, "prob"] = merged.loc[not_listed, "prob"].fillna(0.)

    field_probs = _compute_field_odds(merged)
    merged = merged.merge(field_probs, on=["league", "team"], how="left")
    merged["prob"] = merged["prob"].fillna(merged["field_prob"])
    merged["prob_delta"] = merged["prob_delta"].fillna(merged["field_prob_delta"])

    return merged