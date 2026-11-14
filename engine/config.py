"""Every tunable number in the engine, in one place. All are ASSUMPTIONS to review, not measured facts.

Shown to users with the results (weights) or in the evidence lines (proxies).
"""
# rating -> score (nitrogen fixing, fodder value). Amrita's issue 2: use the rating, not a kg range midpoint.
RATING_SCORE = {"none": 0, "low": 25, "medium": 60, "high": 100}

# Rabi water fit: wet root-zone days (Oct-Dec, POWER GWETROOT >= 0.65) a crop of each water-need rating wants.
# PROXY, no real water balance yet. Replace with a soil-water model.
RABI_WET_DAYS_NEEDED = {"low": 30, "medium": 50, "high": 70}

# Timing penalties (points off 100)
LATE_ONSET_PENALTY = 30          # monsoon starts after the crop's sowing window closes
SOWING_DELAY_FREE_DAYS = 14      # delay beyond window start tolerated before penalty
SOWING_DELAY_PER_DAY = 1.0       # points per day of delay beyond the free days
SOWING_DELAY_CAP = 30
HEAT_SEASON_START_DOY = 74       # 15 March; crop days after this are exposed to pre-monsoon heat
HEAT_EXPOSURE_PER_DAY = 2.0
HEAT_EXPOSURE_CAP = 60

# Mixed crops: water need of the partner crop that adds to the main crop's need (ASSUMPTION)
INTERCROP_PARTNER_WATER_SHARE = 0.30

# Market: score from price / MSP ratio, with a haircut for volatility
MARKET_RATIO_FLOOR = 0.8         # ratio at or below this scores 0
MARKET_RATIO_SPAN = 0.6          # ratio = floor + span scores 100
MARKET_VOLATILITY_CAP = 0.30     # coefficient of variation at or above this takes the full haircut
MARKET_VOLATILITY_MAX_HAIRCUT = 0.30
MARKET_WINDOW_MONTHS = 12

DAYS_IN_YEAR = 365

CURRENT_MSP_SEASON = "2026-27"   # prefer MSP rows whose marketing_season contains this

# Crop sheet name -> name used in the mandi price table
MARKET_CROP_KEY = {"sorghum_kharif": "sorghum", "sorghum_rabi": "sorghum"}

# Hand-off between consecutive crops: points off timing_fit when the first crop finishes after the next
# crop's sowing window has closed (ASSUMPTION)
HANDOFF_PENALTY = 30
