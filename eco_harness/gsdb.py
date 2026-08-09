"""
GSDB v4 — Global Sanctions Database loader.

The GSDB (Global Sanctions Database) is an academic dataset from researchers
at the Ifo Institute / University of Geneva covering 1,500+ sanction cases
across 1950-2024. Distributed as CSV and Stata .dta files.

This module provides a read-only loader for the local GSDB CSV file.
Expected columns: case_id, sanctioned_state, sanctioning_state, begin_year,
  end_year, trade, arms, military, financial, travel, other, target_mult,
  sender_mult, objective, success.

Default path: data/L1_api/GSDB_V4.csv
Override with GSDB_PATH env var.
"""
import os
from pathlib import Path

import pandas as pd

_DEFAULT_DIR = os.environ.get(
    'GSDB_DIR',
    os.path.join(os.path.dirname(__file__), '..', '..', '..',
                 'aed_system', 'aed_sov_dashboard', 'data', 'L1_api')
)

_GSDB_CACHE: pd.DataFrame | None = None


def _resolve_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path)
    return Path(os.environ.get('GSDB_PATH',
               os.path.join(_DEFAULT_DIR, 'GSDB_V4.csv')))


def load(path: str | Path | None = None, force_reload: bool = False) -> pd.DataFrame:
    """Load and cache the GSDB dataset.

    Args:
        path: Path to GSDB CSV. Defaults to GSDB_PATH env var or
              data/L1_api/GSDB_V4.csv.
        force_reload: If True, bypass cache and re-read from disk.

    Returns:
        DataFrame with all GSDB columns. Empty DataFrame if file not found.
    """
    global _GSDB_CACHE
    if _GSDB_CACHE is not None and not force_reload:
        return _GSDB_CACHE

    p = _resolve_path(path)
    if not p.exists():
        print(f'[GSDB] dataset not found: {p}')
        return pd.DataFrame()

    if p.suffix.lower() == '.dta':
        df = pd.read_stata(p)
    else:
        df = pd.read_csv(p)

    # Normalise end_year: GSDB uses 9999 for ongoing sanctions
    if 'end_year' in df.columns:
        current_year = pd.Timestamp.now().year
        df['end_year'] = df['end_year'].replace(9999, current_year)

    _GSDB_CACHE = df
    return df


def sanctions_by_target(target_country: str) -> pd.DataFrame:
    """All sanctions targeting a country.

    Args:
        target_country: Country name as it appears in GSDB (e.g. 'China',
                        'Russia', 'Iran').
    """
    df = load()
    if df.empty:
        return df
    mask = df['sanctioned_state'].str.lower() == target_country.lower()
    return df[mask].reset_index(drop=True)


def sanctions_by_sender(sender_country: str) -> pd.DataFrame:
    """All sanctions imposed by a country.

    Args:
        sender_country: Country name (e.g. 'United States', 'European Union').
    """
    df = load()
    if df.empty:
        return df
    mask = df['sanctioning_state'].str.lower() == sender_country.lower()
    return df[mask].reset_index(drop=True)


def sanctions_by_type(sanction_type: str) -> pd.DataFrame:
    """Filter sanctions by type.

    Args:
        sanction_type: One of 'trade', 'arms', 'military', 'financial',
                       'travel', 'other'. GSDB uses binary columns for each.
    """
    df = load()
    if df.empty:
        return df
    col = sanction_type.lower()
    if col not in df.columns:
        print(f'[GSDB] unknown type: {sanction_type}. '
              f'Available: trade, arms, military, financial, travel, other')
        return pd.DataFrame(columns=df.columns)
    return df[df[col] == 1].reset_index(drop=True)


def active_sanctions(year: int | None = None) -> pd.DataFrame:
    """Sanctions active in a given year (default: current year).

    A sanction is active if begin_year <= year <= end_year.
    """
    df = load()
    if df.empty:
        return df
    y = year or pd.Timestamp.now().year
    mask = (df['begin_year'] <= y) & (df['end_year'] >= y)
    return df[mask].reset_index(drop=True)


def sanctions_summary(target_country: str | None = None,
                      sender_country: str | None = None) -> pd.DataFrame:
    """Pivot-table summary of sanctions counts by target or sender.

    If neither target nor sender is given, returns the full dataset.
    """
    df = load()
    if df.empty:
        return df
    if target_country:
        return sanctions_by_target(target_country)
    if sender_country:
        return sanctions_by_sender(sender_country)
    return df


def sanctions_count_trend(target_country: str) -> pd.DataFrame:
    """Time series: how many sanctions were active against a country per year.

    Returns DataFrame with columns: year, active_count.
    """
    df = sanctions_by_target(target_country)
    if df.empty:
        return df

    min_year = int(df['begin_year'].min())
    max_year = int(df['end_year'].max())

    rows = []
    for y in range(min_year, max_year + 1):
        count = int(((df['begin_year'] <= y) & (df['end_year'] >= y)).sum())
        rows.append({'year': y, 'active_count': count})

    return pd.DataFrame(rows)