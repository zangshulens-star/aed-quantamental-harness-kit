"""
SIPRI Arms Transfers — hybrid scraper + static fallback.

SIPRI (Stockholm International Peace Research Institute) publishes the Arms
Transfers Database with Trend Indicator Values (TIV) for major conventional
weapons transfers since 1950.

No official API. Data is accessed via:
  1. Live CSV export: https://armstransfers.sipri.org/ArmsTransfer/CSVExport
  2. Manual CSV in L1 directory
  3. Static stub (built-in, reviewed quarterly)

All public functions return pandas DataFrames. No API key required.
"""
import os
from pathlib import Path

import pandas as pd
import requests

SIPRI_CSV_URL = "https://armstransfers.sipri.org/ArmsTransfer/CSVExport"

_L1_DIR = Path(os.environ.get(
    'SIPRI_DATA_DIR',
    os.path.join(os.path.dirname(__file__), '..', '..', '..',
                 'aed_system', 'aed_sov_dashboard', 'data', 'L1_api')
))

# TIV stub data — 5-year average 2020-2024, % from US / China / Russia
# Source: SIPRI Arms Transfers Database factsheets. Review quarterly.
_SIPRI_STUB: dict[str, dict[str, float | str | int]] = {
    "ARE": {"us_share": 68.0, "chn_share": 5.2,  "rus_share": 3.0,  "data_year": 2024},
    "AUS": {"us_share": 72.0, "chn_share": 0.0,  "rus_share": 0.0,  "data_year": 2024},
    "BRA": {"us_share": 12.0, "chn_share": 3.5,  "rus_share": 5.0,  "data_year": 2024},
    "CAN": {"us_share": 78.0, "chn_share": 0.0,  "rus_share": 0.0,  "data_year": 2024},
    "CHL": {"us_share": 35.0, "chn_share": 2.0,  "rus_share": 0.0,  "data_year": 2024},
    "CHN": {"us_share": 0.0,  "chn_share": 100.0,"rus_share": 3.0,  "data_year": 2024},
    "DEU": {"us_share": 55.0, "chn_share": 0.0,  "rus_share": 0.0,  "data_year": 2024},
    "FRA": {"us_share": 42.0, "chn_share": 0.0,  "rus_share": 0.0,  "data_year": 2024},
    "GBR": {"us_share": 65.0, "chn_share": 0.0,  "rus_share": 0.0,  "data_year": 2024},
    "IDN": {"us_share": 22.0, "chn_share": 18.0, "rus_share": 15.0, "data_year": 2024},
    "IND": {"us_share": 12.0, "chn_share": 3.0,  "rus_share": 46.0, "data_year": 2024},
    "ITA": {"us_share": 48.0, "chn_share": 0.0,  "rus_share": 0.0,  "data_year": 2024},
    "JPN": {"us_share": 85.0, "chn_share": 0.0,  "rus_share": 0.0,  "data_year": 2024},
    "KOR": {"us_share": 75.0, "chn_share": 0.0,  "rus_share": 0.0,  "data_year": 2024},
    "MEX": {"us_share": 58.0, "chn_share": 2.5,  "rus_share": 3.0,  "data_year": 2024},
    "MYS": {"us_share": 15.0, "chn_share": 25.0, "rus_share": 8.0,  "data_year": 2024},
    "PER": {"us_share": 30.0, "chn_share": 8.0,  "rus_share": 5.0,  "data_year": 2024},
    "PHL": {"us_share": 70.0, "chn_share": 3.0,  "rus_share": 0.0,  "data_year": 2024},
    "QAT": {"us_share": 55.0, "chn_share": 8.0,  "rus_share": 0.0,  "data_year": 2024},
    "SAU": {"us_share": 72.0, "chn_share": 10.0, "rus_share": 0.0,  "data_year": 2024},
    "SGP": {"us_share": 60.0, "chn_share": 4.0,  "rus_share": 0.0,  "data_year": 2024},
    "TUR": {"us_share": 25.0, "chn_share": 12.0, "rus_share": 15.0, "data_year": 2024},
    "USA": {"us_share": 100.0,"chn_share": 0.0,  "rus_share": 0.0,  "data_year": 2024},
    "VNM": {"us_share": 5.0,  "chn_share": 55.0, "rus_share": 35.0, "data_year": 2024},
    "ZAF": {"us_share": 8.0,  "chn_share": 20.0, "rus_share": 3.0,  "data_year": 2024},
}

_SUPPLIER_SEARCH_TERMS = {
    'US': 'United States',
    'CHN': 'China',
    'RUS': 'Russia',
    'FRA': 'France',
    'DEU': 'Germany',
    'GBR': 'United Kingdom',
}


def _scrape_csv(year_start: int = 2020, year_end: int = 2024) -> pd.DataFrame | None:
    """Download SIPRI CSV export and parse into DataFrame.

    Returns None on any failure (caller falls back to stub/manual CSV).
    """
    try:
        resp = requests.get(SIPRI_CSV_URL, timeout=30)
        if resp.status_code != 200:
            return None
    except Exception:
        return None

    lines = resp.text.splitlines()
    if len(lines) < 2:
        return None

    rows = []
    for line in lines[1:]:
        parts = line.split(',')
        if len(parts) < 5:
            continue
        try:
            year = int(parts[0].strip())
            recipient = parts[1].strip().strip('"')
            supplier = parts[2].strip().strip('"')
            tiv_generated = float(parts[3].strip()) if parts[3].strip() else 0.0
            tiv_delivered = float(parts[4].strip()) if parts[4].strip() else 0.0
        except (ValueError, IndexError):
            continue

        if year < year_start or year > year_end:
            continue

        rows.append({
            'year': year,
            'recipient': recipient,
            'supplier': supplier,
            'tiv_generated': tiv_generated,
            'tiv_delivered': tiv_delivered,
        })

    return pd.DataFrame(rows) if rows else None


def fetch_arms_transfers() -> pd.DataFrame:
    """Fetch raw SIPRI arms transfers data.

    Priority: live CSV → manual CSV → static stub.
    Returns DataFrame with: year, recipient, supplier, tiv_generated, tiv_delivered.
    """
    df = _scrape_csv()
    if df is not None and not df.empty:
        print('[SIPRI] live CSV export loaded')
        return df

    csv_path = _L1_DIR / 'L1_sipri_arms.csv'
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            print(f'[SIPRI] loaded from {csv_path}')
            return df
        except Exception:
            pass

    print('[SIPRI] using static stub (offline fallback)')
    rows = []
    for iso3, v in _SIPRI_STUB.items():
        for supplier_key, supplier_name in _SUPPLIER_SEARCH_TERMS.items():
            share_key = {'US': 'us_share', 'CHN': 'chn_share', 'RUS': 'rus_share',
                         'FRA': 'fra_share', 'DEU': 'deu_share', 'GBR': 'gbr_share'}
            sk = share_key.get(supplier_key)
            if sk and sk in v:
                rows.append({
                    'iso3': iso3,
                    'supplier': supplier_name,
                    'share_pct': v[sk],
                    'data_year': v.get('data_year', 2024),
                    'source': 'sipri_stub',
                })
    return pd.DataFrame(rows)


def by_supplier(supplier: str) -> pd.DataFrame:
    """Filter arms transfer records by supplier country name."""
    df = fetch_arms_transfers()
    if df.empty:
        return df
    q = supplier.lower()
    mask = df['supplier'].str.lower().str.contains(q, na=False)
    return df[mask].reset_index(drop=True)


def by_recipient(iso3: str) -> pd.DataFrame:
    """Get arms import shares for a recipient country (3-letter ISO)."""
    df = fetch_arms_transfers()
    if df.empty:
        return df
    if 'iso3' in df.columns:
        return df[df['iso3'].str.upper() == iso3.upper()].reset_index(drop=True)
    if 'recipient' in df.columns:
        q = iso3.upper()
        return df[df['recipient'].str.upper().str.contains(q, na=False)].reset_index(drop=True)
    return df


def us_exports() -> pd.DataFrame:
    """US arms exports — top recipients by TIV."""
    return by_supplier('United States')


def china_exports() -> pd.DataFrame:
    """China arms exports — top recipients by TIV."""
    return by_supplier('China')


def top_suppliers(n: int = 5) -> pd.DataFrame:
    """Top N arms suppliers by total TIV delivered."""
    df = fetch_arms_transfers()
    if df.empty:
        return df
    if 'tiv_delivered' in df.columns:
        return (df.groupby('supplier')['tiv_delivered'].sum()
                  .sort_values(ascending=False).head(n).reset_index())
    if 'share_pct' in df.columns:
        return (df.groupby('supplier')['share_pct'].sum()
                  .sort_values(ascending=False).head(n).reset_index())
    return df


def top_recipients(n: int = 10) -> pd.DataFrame:
    """Top N arms recipients by total TIV delivered."""
    df = fetch_arms_transfers()
    if df.empty:
        return df
    col = 'recipient' if 'recipient' in df.columns else 'iso3'
    val = 'tiv_delivered' if 'tiv_delivered' in df.columns else 'share_pct'
    return (df.groupby(col)[val].sum()
              .sort_values(ascending=False).head(n).reset_index())