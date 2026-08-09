"""
BIS Statistics Harness — Bank for International Settlements data via SDMX-ML.

BIS serves XML-only (no JSON/CSV). This harness fetches and parses SDMX-ML
into pandas DataFrames. No API key required.

Key dataflows:
  - WS_CPP: Credit to Private Non-financial Sector (core macro)
  - WS_TC: Total Credit
  - WS_CBP: Commercial Bank Positions
"""
import xml.etree.ElementTree as ET
from io import StringIO

import pandas as pd
import requests

BIS_BASE = "https://stats.bis.org/api/v2"


def _parse_sdmx_xml(xml_bytes: bytes) -> pd.DataFrame:
    """Parse BIS SDMX-ML StructureSpecificData into a pandas DataFrame."""
    root = ET.fromstring(xml_bytes)

    # Find all Series + Obs — strip namespaces
    rows = []
    for series in root.iter():
        if 'Series' not in series.tag.split('}')[-1]:
            continue
        # Series-level dimension attributes
        series_dims = dict(series.attrib)
        for obs in series:
            tag = obs.tag.split('}')[-1]
            if tag == 'Obs':
                row = dict(series_dims)
                row.update(dict(obs.attrib))
                rows.append(row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    if 'OBS_VALUE' in df.columns:
        df['OBS_VALUE'] = pd.to_numeric(df['OBS_VALUE'], errors='coerce')
    return df


def fetch(dataflow: str = "WS_CPP", ref_area: str = None,
          freq: str = None, start_period: str = None,
          end_period: str = None) -> pd.DataFrame:
    """Fetch BIS dataflow and return as pandas DataFrame.

    Args:
        dataflow: BIS dataflow ID (e.g. 'WS_CPP', 'WS_TC').
        ref_area: ISO 3166-1 alpha-2 country code or list (e.g. 'US' or ['US','CN','JP']).
        freq: 'Q' quarterly, 'A' annual, 'M' monthly.
        start_period / end_period: Time bounds (e.g. '2020' or '2020-Q1').

    Returns:
        DataFrame with columns: FREQ, REF_AREA, TIME_PERIOD, OBS_VALUE, etc.
    """
    url = f"{BIS_BASE}/data/dataflow/BIS/{dataflow}/1.0"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    df = _parse_sdmx_xml(resp.content)

    # Filter
    if ref_area:
        if isinstance(ref_area, str):
            ref_area = [ref_area]
        df = df[df['REF_AREA'].isin(ref_area)]
    if freq:
        df = df[df['FREQ'] == freq]
    if start_period:
        df = df[df['TIME_PERIOD'] >= start_period]
    if end_period:
        df = df[df['TIME_PERIOD'] <= end_period]

    return df.reset_index(drop=True)


# BIS uses non-standard ISO codes for some countries
BIS_COUNTRY_MAP = {
    'CN': 'CN',   # China works in BIS
    'US': 'US',
    'JP': 'JP',
    'DE': 'DE',
    'GB': 'GB',
    'FR': 'FR',
    'IT': 'IT',
    'KR': 'KR',
    'BR': 'BR',
    'IN': 'IN',
    'CA': 'CA',
    'AU': 'AU',
    'CH': 'CH',
    'ES': 'ES',
    'MX': 'MX',
    'NL': 'NL',
    'SE': 'SE',
    'RU': 'RU',
}


def credit_private(countries=None, freq='Q'):
    """Credit to Private Non-financial Sector (as % of GDP).

    Core macro indicator — total credit to households and non-financial firms.
    """
    if countries:
        countries = [BIS_COUNTRY_MAP.get(c, c) for c in (countries if isinstance(countries, list) else [countries])]
    df = fetch('WS_CPP', ref_area=countries, freq=freq)
    return df


def total_credit(countries=None, freq='Q'):
    """Total Credit (all sectors, % of GDP)."""
    if countries:
        countries = [BIS_COUNTRY_MAP.get(c, c) for c in (countries if isinstance(countries, list) else [countries])]
    df = fetch('WS_TC', ref_area=countries, freq=freq)
    return df


def property_prices(countries=None, freq='Q'):
    """Residential Property Prices (selected countries)."""
    if countries:
        countries = [BIS_COUNTRY_MAP.get(c, c) for c in (countries if isinstance(countries, list) else [countries])]
    df = fetch('WS_RPP', ref_area=countries, freq=freq)
    return df


def list_countries(dataflow='WS_CPP'):
    """Return all available country codes in a dataflow."""
    df = fetch(dataflow)
    return sorted(df['REF_AREA'].unique())
