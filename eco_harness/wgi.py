"""
Worldwide Governance Indicators (WGI) Harness — direct REST + JSON.

WGI is World Bank source 3, 36 indicators (6 dimensions x 6 variants each).
Indicator codes use GOV_WGI_ prefix (changed from old CC.EST/GE.EST format).

6 core dimensions (estimate variant, approx -2.5 to +2.5):
  - GOV_WGI_CC.EST: Control of Corruption
  - GOV_WGI_GE.EST: Government Effectiveness
  - GOV_WGI_PV.EST: Political Stability and Absence of Violence
  - GOV_WGI_RQ.EST: Regulatory Quality
  - GOV_WGI_RL.EST: Rule of Law
  - GOV_WGI_VA.EST: Voice and Accountability

Other variants per dimension: .SC (score 0-100), .SC_LB/.SC_UB (confidence bounds),
.SE (standard error), .SR (number of sources).

No API key required. Data typically covers 1996-2024.
"""
import pandas as pd
import requests

WB_BASE = "https://api.worldbank.org/v2"

# Core 6 indicators (estimate variant)
WGI_INDICATORS = {
    'CC': 'GOV_WGI_CC.EST',   # Control of Corruption
    'GE': 'GOV_WGI_GE.EST',   # Government Effectiveness
    'PV': 'GOV_WGI_PV.EST',   # Political Stability
    'RQ': 'GOV_WGI_RQ.EST',   # Regulatory Quality
    'RL': 'GOV_WGI_RL.EST',   # Rule of Law
    'VA': 'GOV_WGI_VA.EST',   # Voice and Accountability
}


def get_indicator(indicator: str, country: str = 'USA',
                  date_range: str = None) -> pd.DataFrame:
    """Fetch a WGI indicator for a country.

    Args:
        indicator: Short key ('CC','GE','PV','RQ','RL','VA') or full code.
        country: ISO 3166-1 alpha-3 country code.
        date_range: e.g. '2010:2024'.

    Returns:
        DataFrame with 'date' and 'value' columns.
    """
    code = WGI_INDICATORS.get(indicator, indicator)
    params = {'format': 'json', 'per_page': 50}
    if date_range:
        params['date'] = date_range

    resp = requests.get(f"{WB_BASE}/country/{country}/indicator/{code}",
                       params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if len(data) < 2 or not data[1]:
        return pd.DataFrame(columns=['date', 'value'])

    rows = [{'date': d['date'], 'value': float(d['value']) if d['value'] else None}
            for d in data[1]]
    df = pd.DataFrame(rows)
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date').reset_index(drop=True)


def get_all_wgi(country: str = 'USA') -> pd.DataFrame:
    """Fetch all 6 core WGI indicators for a country.

    Returns DataFrame with columns: date, indicator, value.
    """
    frames = []
    for key, code in WGI_INDICATORS.items():
        df = get_indicator(key, country)
        if not df.empty:
            df['indicator'] = key
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=['date', 'indicator', 'value'])
    return pd.concat(frames, ignore_index=True)
