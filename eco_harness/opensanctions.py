"""
OpenSanctions — consolidated sanctions entity CSV loader.

OpenSanctions aggregates sanctions lists from 85+ sources (UN, EU, OFAC, UK,
etc.) into a unified dataset. This module loads pre-downloaded CSV exports from
a local path — no API calls, no authentication.

Expected CSV columns (summary):
  iso3, iso2, total_entities, us_entities, un_entities, eu_entities,
  uk_entities, other_entities, unique_program_count, top_programs

Expected CSV columns (entities):
  iso3, name, dataset, program_ids, sender, first_seen, last_seen

Default lookup path: data/L1_api/L1_opensanctions_*.csv
Override with OS_SANCTIONS_DIR env var.
"""
import os
import json
from pathlib import Path

import pandas as pd

_DEFAULT_DIR = os.environ.get(
    'OS_SANCTIONS_DIR',
    os.path.join(os.path.dirname(__file__), '..', '..', '..',
                 'aed_system', 'aed_sov_dashboard', 'data', 'L1_api')
)


def _resolve_dir() -> Path:
    return Path(os.environ.get('OS_SANCTIONS_DIR', _DEFAULT_DIR))


def load_summary(path: str | Path | None = None) -> pd.DataFrame:
    """Load per-country sanctions summary CSV.

    Returns DataFrame with columns: iso3, iso2, total_entities, us_entities,
    un_entities, eu_entities, uk_entities, other_entities, unique_program_count,
    top_programs.
    """
    if path is None:
        path = _resolve_dir() / 'L1_opensanctions_25_country_summary.csv'
    path = Path(path)
    if not path.exists():
        print(f'[OpenSanctions] summary not found: {path}')
        return pd.DataFrame()
    df = pd.read_csv(path)
    if 'top_programs' in df.columns:
        df['top_programs'] = df['top_programs'].apply(
            lambda x: json.loads(x) if isinstance(x, str) and x.startswith('[') else x
        )
    return df


def load_entities(path: str | Path | None = None) -> pd.DataFrame:
    """Load per-entity sanctions CSV.

    Returns DataFrame with columns: iso3, name, dataset, program_ids, sender,
    first_seen, last_seen.
    """
    if path is None:
        path = _resolve_dir() / 'L1_opensanctions_25_country_entities.csv'
    path = Path(path)
    if not path.exists():
        print(f'[OpenSanctions] entities not found: {path}')
        return pd.DataFrame()
    return pd.read_csv(path)


def search_by_country(iso3: str) -> pd.DataFrame:
    """Return all sanctioned entities for a country (3-letter ISO code)."""
    df = load_entities()
    if df.empty:
        return df
    return df[df['iso3'].str.upper() == iso3.upper()].reset_index(drop=True)


def search_by_name(query: str) -> pd.DataFrame:
    """Case-insensitive partial name search across all sanctioned entities."""
    df = load_entities()
    if df.empty:
        return df
    q = query.lower()
    mask = df['name'].str.lower().str.contains(q, na=False)
    return df[mask].reset_index(drop=True)


def search_by_sender(sender: str) -> pd.DataFrame:
    """Filter entities by sanctioning authority (e.g. 'US', 'UN', 'EU', 'UK')."""
    df = load_entities()
    if df.empty:
        return df
    s = sender.upper()
    mask = df['sender'].str.upper().str.contains(s, na=False)
    return df[mask].reset_index(drop=True)


def sanctions_summary(iso3: str | None = None) -> pd.DataFrame:
    """Return summary DataFrame. If iso3 given, filter to single country."""
    df = load_summary()
    if df.empty:
        return df
    if iso3:
        df = df[df['iso3'].str.upper() == iso3.upper()]
    return df.reset_index(drop=True)


def entity_count() -> int:
    """Total number of sanctioned entities across the loaded dataset."""
    df = load_entities()
    return len(df) if not df.empty else 0