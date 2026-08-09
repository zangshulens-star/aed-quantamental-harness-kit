"""
IMF COFER — Currency Composition of Official Foreign Exchange Reserves.

COFER (Currency Composition of Official Foreign Exchange Reserves) is a
quarterly IMF dataset showing the currency breakdown of global central-bank
reserve holdings. This is a key indicator for USD hegemony / de-dollarisation.

Data accessed via IMF SDMX REST API (public, no key required).
Endpoint: https://sdmxcentral.imf.org/ws/public/sdmxjson/rest/data/IMF,COFER,1.0/

Returns standardised pandas DataFrames.
"""
import pandas as pd
import requests

IMF_SDMX_BASE = "https://sdmxcentral.imf.org/ws/public/sdmxjson/rest/data"
COFER_DATAFLOW = "IMF,COFER,1.0"

# COFER publishes claims in 8 currencies + "Other" + "Unallocated"
# Key currency dimension values:
CURRENCY_CODES = {
    'USD': 'Claims in U.S. dollars',
    'EUR': 'Claims in euros',
    'JPY': 'Claims in Japanese yen',
    'GBP': 'Claims in pounds sterling',
    'CNY': 'Claims in Chinese renminbi',
    'CAD': 'Claims in Canadian dollars',
    'AUD': 'Claims in Australian dollars',
    'CHF': 'Claims in Swiss francs',
    'OTH': 'Claims in other currencies',
    'UAL': 'Unallocated Reserves',
    'TAL': 'Total Allocated Reserves',
}

# IMF SDMX series keys for the main COFER indicators
# Q = quarterly, USD = claims in US dollars, XDC = share in allocated reserves
COFER_SERIES = {
    'total_allocated': 'Q..TAL_XDC_USD',
    'usd_share': 'Q..USD_XDC_USD',
    'eur_share': 'Q..EUR_XDC_USD',
    'jpy_share': 'Q..JPY_XDC_USD',
    'gbp_share': 'Q..GBP_XDC_USD',
    'cny_share': 'Q..CNY_XDC_USD',
    'cad_share': 'Q..CAD_XDC_USD',
    'aud_share': 'Q..AUD_XDC_USD',
    'chf_share': 'Q..CHF_XDC_USD',
    'oth_share': 'Q..OTH_XDC_USD',
}


def _fetch_cofer_sdmx(series_key: str) -> pd.DataFrame:
    """Fetch a COFER series from IMF SDMX.

    Args:
        series_key: COFER series dimension key (e.g. 'Q..USD_XDC_USD').

    Returns:
        DataFrame with columns: date, value.
    """
    url = f"{IMF_SDMX_BASE}/{COFER_DATAFLOW}/{series_key}"
    params = {'format': 'compact_v2'}

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f'[COFER] SDMX fetch failed: {e}')
        return pd.DataFrame(columns=['date', 'value'])

    data = resp.json()
    return _parse_sdmx_compact(data)


def _parse_sdmx_compact(data: dict) -> pd.DataFrame:
    """Parse IMF SDMX compact_v2 JSON into date/value DataFrame."""
    try:
        ds = data.get('dataSets', [{}])[0]
        series = ds.get('series', {})
        obs = series.get('0:0:0:0', {}).get('observations', {})
        if not obs:
            # Try keys-ordered observation list
            for val in series.values():
                if isinstance(val, dict) and 'observations' in val:
                    obs = val['observations']
                    break

        structure = data.get('structure', {})
        dims = structure.get('dimensions', {})
        obs_list = dims.get('observation', [])

        # Find time dimension index
        time_idx = None
        for i, obs_dim in enumerate(obs_list):
            if obs_dim.get('id') == 'TIME_PERIOD':
                time_idx = i

        rows = []
        for idx_str, vals in obs.items():
            idx_parts = idx_str.split(':')
            if time_idx is not None and len(idx_parts) > time_idx:
                time_val = idx_parts[time_idx]
            else:
                time_val = idx_str

            if isinstance(vals, list) and len(vals) > 0:
                row_val = vals[0]
            elif isinstance(vals, (int, float)):
                row_val = vals
            else:
                continue

            rows.append({'date': str(time_val), 'value': float(row_val)})

        if not rows:
            # Fallback: try flat observations (non-keyed)
            for idx_str, vals in obs.items():
                if isinstance(vals, list):
                    for i, v in enumerate(vals):
                        rows.append({'date': str(i), 'value': float(v)})
                elif isinstance(vals, (int, float)):
                    rows.append({'date': str(idx_str), 'value': float(vals)})

        return pd.DataFrame(rows).sort_values('date').reset_index(drop=True)
    except Exception as e:
        print(f'[COFER] parse error: {e}')
        return pd.DataFrame(columns=['date', 'value'])


def _alternative_cofer_fetch() -> pd.DataFrame:
    """Fallback: try the IMF data API with alternate URL pattern."""
    try:
        url = ("http://dataservices.imf.org/REST/SDMX_JSON.svc/"
               "CompactData/COFER/A.US.USD_Share_in_Allocated_Reserves")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        ds = data.get('CompactData', {}).get('DataSet', {})
        series_data = ds.get('Series', {})
        obs = series_data.get('Obs', [])

        rows = []
        for o in obs:
            rows.append({
                'date': o.get('@TIME_PERIOD', ''),
                'value': float(o.get('@OBS_VALUE', 0)),
            })

        if rows:
            return pd.DataFrame(rows).sort_values('date').reset_index(drop=True)
    except Exception:
        pass
    return pd.DataFrame(columns=['date', 'value'])


def _get_series(series_key: str) -> pd.DataFrame:
    """Try primary SDMX, fall back to alternative endpoint."""
    df = _fetch_cofer_sdmx(series_key)
    if df.empty or len(df) == 0:
        df = _alternative_cofer_fetch()
    return df


def usd_share() -> pd.DataFrame:
    """USD share of total allocated FX reserves (%).

    Returns DataFrame with columns: date, value.
    """
    df = _get_series(COFER_SERIES['usd_share'])
    if df.empty:
        print('[COFER] unable to fetch USD share — IMF endpoint may have changed.'
              ' Check https://data.imf.org/cofer for manual download.')
    return df


def total_allocated_reserves() -> pd.DataFrame:
    """Total allocated reserves in USD.

    Returns DataFrame with columns: date, value.
    """
    return _get_series(COFER_SERIES['total_allocated'])


def currency_shares() -> pd.DataFrame:
    """All currency shares as % of allocated reserves.

    Returns DataFrame with columns: date, USD, EUR, JPY, GBP, CNY, CAD, AUD, CHF, Other.
    """
    currencies = ['USD', 'EUR', 'JPY', 'GBP', 'CNY', 'CAD', 'AUD', 'CHF', 'OTH']
    frames = {}

    for cur in currencies:
        key = f'Q..{cur}_XDC_USD'
        df = _get_series(key)
        if not df.empty:
            df = df.rename(columns={'value': cur})
            frames[cur] = df.set_index('date')[cur]

    if not frames:
        return pd.DataFrame()

    result = pd.DataFrame(frames).reset_index()
    result = result.rename(columns={'index': 'date'})
    return result.sort_values('date').reset_index(drop=True)


def cny_share_trend() -> pd.DataFrame:
    """CNY/RMB share of allocated reserves — key de-dollarisation indicator.

    Returns DataFrame with columns: date, value.
    """
    return _get_series(COFER_SERIES['cny_share'])
