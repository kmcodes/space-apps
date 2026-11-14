"""Market component: a PRICE SIGNAL, not income (no yields or costs here).

Last 12 months of district mandi modal prices against MSP, with a haircut for volatility.
No mandi rows -> gap (an MSP alone would look perfectly stable, which would mislead).
"""
import pandas as pd

from . import config
from .components import Result
from .validity import worst


def market_score(ratio, volatility):
    base = 100.0 * (ratio - config.MARKET_RATIO_FLOOR) / config.MARKET_RATIO_SPAN
    base = min(100.0, max(0.0, base))
    haircut = config.MARKET_VOLATILITY_MAX_HAIRCUT * min(volatility, config.MARKET_VOLATILITY_CAP) / config.MARKET_VOLATILITY_CAP
    return base * (1 - haircut)


def _gap(reason):
    return Result(None, "missing", "unverified", {"reason": reason})


class MarketData:
    def __init__(self, mandi: pd.DataFrame, msp: pd.DataFrame):
        self.mandi = mandi
        self.msp = msp

    def _msp_row(self, crop):
        rows = self.msp[self.msp.crop == crop]
        if rows.empty:
            return None
        current = rows[rows.marketing_season.str.contains(config.CURRENT_MSP_SEASON)]
        rows = current if not current.empty else rows
        valid = rows[rows.validity == "valid"]
        return (valid if not valid.empty else rows).iloc[0]

    def component(self, point, crop):
        if crop == "fallow":
            return Result(None, "na", "valid", {"reason": "fallow earns nothing; not scored"})
        crop = config.MARKET_CROP_KEY.get(crop, crop)
        msp = self._msp_row(crop)
        rows = self.mandi[(self.mandi.point == point) & (self.mandi.crop == crop)]
        if rows.empty:
            return _gap("no mandi price data (MSP only)" if msp is not None else "no mandi price or MSP data")
        if msp is None:
            return _gap("no MSP for this crop")
        window = sorted(rows.month.unique())[-config.MARKET_WINDOW_MONTHS:]
        prices = rows[rows.month.isin(window)].median_modal_price.astype(float)
        price = float(prices.median())
        vol = float(prices.std(ddof=0) / prices.mean()) if prices.mean() else 0.0
        ratio = price / float(msp.msp_rs_per_quintal)
        return Result(market_score(ratio, vol), "ok", worst("valid", msp.validity),
                      {"ratio": ratio, "price_rs_per_quintal": price, "msp_rs_per_quintal": float(msp.msp_rs_per_quintal),
                       "volatility": vol, "months": len(window), "msp_season": msp.marketing_season})


def load_market(mandi_path, msp_path):
    return MarketData(pd.read_csv(mandi_path), pd.read_csv(msp_path))
