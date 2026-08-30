"""Hard-coded corpus: the 5 Groww URLs only (PRD §4)."""

FUNDS = [
    {
        "category": "Large-cap",
        "fund_label": "HDFC Large Cap Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        "slug": "hdfc-large-cap-fund-direct-growth",
    },
    {
        "category": "Flexi-cap",
        "fund_label": "HDFC Flexi Cap Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
        "slug": "hdfc-equity-fund-direct-growth",
    },
    {
        "category": "ELSS",
        "fund_label": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
        "url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        "slug": "hdfc-elss-tax-saver-fund-direct-plan-growth",
    },
    {
        "category": "Small-cap",
        "fund_label": "HDFC Small Cap Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
        "slug": "hdfc-small-cap-fund-direct-growth",
    },
    {
        "category": "Hybrid",
        "fund_label": "HDFC Balanced Advantage Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
        "slug": "hdfc-balanced-advantage-fund-direct-growth",
    },
]

ALLOWED_URLS = {f["url"] for f in FUNDS}
