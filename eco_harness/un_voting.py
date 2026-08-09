"""
UN Voting Data Harness — UNGA ideal point estimates via Harvard Dataverse.

UN Digital Library API requires authentication (403 for guest/search).
This harness uses Voeten et al.'s UNGA ideal point dataset from Harvard Dataverse:
  https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/LEJUQZ

The ideal point estimates measure each country's voting alignment with the
US-led liberal international order (higher = more aligned with US/Western positions).

Data spans 1946-2025. Updated annually. ~1MB tab-separated file.

Data used by C10 (QEGRS geopolitical risk) and C26 (UN voting raw).
"""
import io

import pandas as pd
import requests

# Voeten UNGA Ideal Point Estimates (1946-2025)
# Harvard Dataverse file ID — stable across dataset updates
IDEAL_POINT_FILE_ID = "13642025"
IDEAL_POINT_URL = f"https://dataverse.harvard.edu/api/access/datafile/{IDEAL_POINT_FILE_ID}"

# Full dataset metadata
DATAVERSE_DOI = "doi:10.7910/DVN/LEJUQZ"
DATAVERSE_API = "https://dataverse.harvard.edu/api"


def fetch_ideal_points() -> pd.DataFrame:
    """Download and parse UNGA ideal point estimates (1946-2025).

    Returns DataFrame with: ccode, iso3c, Countryname, year, NVotesFP,
    IdealPointFP, Q5%FP, Q10%FP, Q50%FP, Q90%FP, Q95%FP.
    """
    resp = requests.get(IDEAL_POINT_URL, timeout=60)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text), sep='\t')
    df.columns = df.columns.str.strip()
    return df


def get_ideal_point(iso3: str, min_year: int = 2020) -> pd.DataFrame:
    """Get UNGA ideal point estimates for a specific country.

    Args:
        iso3: ISO 3166-1 alpha-3 code (e.g. 'USA', 'CHN', 'RUS').
        min_year: Earliest year to include (default 2020).

    Returns DataFrame with year, ideal_point, votes_count, confidence_interval.
    """
    df = fetch_ideal_points()
    country_df = df[(df['iso3c'] == iso3) & (df['year'] >= min_year)].copy()
    if country_df.empty:
        return pd.DataFrame(columns=['year', 'ideal_point', 'votes_count',
                                     'ci_lower', 'ci_upper'])
    country_df = country_df.rename(columns={
        'IdealPointFP': 'ideal_point',
        'NVotesFP': 'votes_count',
        'Q5%FP': 'ci_lower',
        'Q95%FP': 'ci_upper',
    })
    return country_df[['year', 'ideal_point', 'votes_count', 'ci_lower', 'ci_upper']].reset_index(drop=True)


def get_ideal_points_multi(iso3_list: list, min_year: int = 2020) -> pd.DataFrame:
    """Get ideal points for multiple countries.

    Args:
        iso3_list: List of ISO3 codes.
        min_year: Earliest year.

    Returns DataFrame with iso3, year, ideal_point, votes_count.
    """
    df = fetch_ideal_points()
    mask = (df['iso3c'].isin(iso3_list)) & (df['year'] >= min_year)
    result = df[mask].copy()
    result = result.rename(columns={
        'iso3c': 'iso3',
        'IdealPointFP': 'ideal_point',
        'NVotesFP': 'votes_count',
        'Q5%FP': 'ci_lower',
        'Q95%FP': 'ci_upper',
    })
    return result[['iso3', 'year', 'ideal_point', 'votes_count',
                   'ci_lower', 'ci_upper']].reset_index(drop=True)


def get_unga_alignment_2025() -> pd.DataFrame:
    """Get latest (2025) ideal point alignment for all countries.

    Returns DataFrame with: iso3, country_name, ideal_point, votes_count.
    Sorted by ideal_point descending (most US-aligned first).
    """
    df = fetch_ideal_points()
    latest = df[df['year'] == df['year'].max()].copy()
    latest = latest.rename(columns={
        'iso3c': 'iso3',
        'Countryname': 'country_name',
        'IdealPointFP': 'ideal_point',
        'NVotesFP': 'votes_count',
    })
    result = latest[['iso3', 'country_name', 'ideal_point', 'votes_count']]
    return result.sort_values('ideal_point', ascending=False).reset_index(drop=True)


def get_voting_distance(iso3_a: str, iso3_b: str = 'USA') -> pd.DataFrame:
    """Calculate UN voting distance between two countries over time.

    Args:
        iso3_a: First country ISO3.
        iso3_b: Second country ISO3 (default 'USA').

    Returns DataFrame with year, distance (absolute ideal point difference).
    """
    df = fetch_ideal_points()
    a = df[df['iso3c'] == iso3_a][['year', 'IdealPointFP']].copy()
    b = df[df['iso3c'] == iso3_b][['year', 'IdealPointFP']].copy()
    merged = a.merge(b, on='year', suffixes=('_a', '_b'))
    merged['distance'] = abs(merged['IdealPointFP_a'] - merged['IdealPointFP_b'])
    merged = merged.rename(columns={
        'IdealPointFP_a': f'ideal_point_{iso3_a}',
        'IdealPointFP_b': f'ideal_point_{iso3_b}',
    })
    return merged.sort_values('year').reset_index(drop=True)


def get_sovereign_ideal_points(min_year: int = 2020) -> pd.DataFrame:
    """Get ideal points for 25 sovereign risk countries.

    Returns DataFrame with iso3, year, ideal_point, votes_count.
    """
    SOVEREIGN_ISO3 = [
        'USA', 'GBR', 'JPN', 'DEU', 'FRA', 'ITA', 'CAN', 'AUS', 'KOR',
        'ESP', 'NLD', 'CHE', 'SWE', 'BEL', 'AUT',
        'CHN', 'IND', 'BRA', 'MEX', 'IDN', 'TUR', 'ZAF', 'RUS', 'SAU', 'ARG',
    ]
    return get_ideal_points_multi(SOVEREIGN_ISO3, min_year=min_year)
