import pandas as pd


def prob2hex(val: float, target_hex="#15eb80"):

    if (isinstance(val, str) and not val) or pd.isna(val):
        return "color: white"

    ratio = float(val) / 50 if float(val) <= 50 else 1
    target_hex = target_hex.lstrip('#')
    tr, tg, tb = (
        int(target_hex[0:2], 16),
        int(target_hex[2:4], 16),
        int(target_hex[4:6], 16),
    )

    # Interpolate from white (255,255,255) to target
    r = round(255 + (tr - 255) * ratio)
    g = round(255 + (tg - 255) * ratio)
    b = round(255 + (tb - 255) * ratio)

    return f"color: #{r:02x}{g:02x}{b:02x}"