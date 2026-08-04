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

def prob2hex_new(val: float, min_hex="#eb1515", max_hex="#15eb80", scale=5):

    if (isinstance(val, str) and not val) or pd.isna(val):
        return "color: white"

    val = float(val)

    if val >= 0:
        ratio = min(val / scale, 1)
        start_hex = "#ffffff"
        end_hex = max_hex
    else:
        ratio = min(-val / scale, 1)
        start_hex = "#ffffff"
        end_hex = min_hex

    start_hex = start_hex.lstrip('#')
    end_hex = end_hex.lstrip('#')

    r1, g1, b1 = (
        int(start_hex[0:2], 16),
        int(start_hex[2:4], 16),
        int(start_hex[4:6], 16),
    )
    r2, g2, b2 = (
        int(end_hex[0:2], 16),
        int(end_hex[2:4], 16),
        int(end_hex[4:6], 16),
    )

    r = round(r1 + (r2 - r1) * ratio)
    g = round(g1 + (g2 - g1) * ratio)
    b = round(b1 + (b2 - b1) * ratio)

    return f"color: #{r:02x}{g:02x}{b:02x}"