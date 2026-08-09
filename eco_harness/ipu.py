"""
IPU Parline Harness — parliamentary data via IPU Parline API v1.

New API base: https://api.data.ipu.org/v1/
JSON:API format with pagination. No API key required.

Key endpoints:
  - GET /v1/countries/{code}  → country info + ISO codes
  - GET /v1/chambers          → chamber details (members, elections)
  - GET /v1/parliaments       → parliament-level data

Data used by C07 (QVOTE political structure) and sovereign risk pipeline.
"""
import pandas as pd
import requests

IPU_BASE = "https://api.data.ipu.org/v1"

# 25 sovereign risk countries — ISO2 codes (aligned with frontend QSERA_DATA_V1.json)
SOVEREIGN_COUNTRIES = {
    'ARE': 'AE', 'AUS': 'AU', 'BRA': 'BR', 'CAN': 'CA', 'CHL': 'CL',
    'CHN': 'CN', 'DEU': 'DE', 'FRA': 'FR', 'GBR': 'GB', 'IDN': 'ID',
    'IND': 'IN', 'ITA': 'IT', 'JPN': 'JP', 'KOR': 'KR', 'MEX': 'MX',
    'MYS': 'MY', 'PER': 'PE', 'PHL': 'PH', 'QAT': 'QA', 'SAU': 'SA',
    'SGP': 'SG', 'TUR': 'TR', 'USA': 'US', 'VNM': 'VN', 'ZAF': 'ZA',
}

# Map IPU chamber_type terms
CHAMBER_TYPE_MAP = {
    'lower_chamber': 'Lower House',
    'upper_chamber': 'Upper House',
    'unicameral': 'Unicameral',
}


def _ipu_get(path: str, params: dict = None) -> dict:
    """GET from IPU API, return parsed JSON."""
    params = params or {}
    params.setdefault('page[size]', 300)
    resp = requests.get(f"{IPU_BASE}{path}", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _parse_time_series(value) -> any:
    """IPU returns many fields as time-series lists. Extract latest value."""
    if isinstance(value, list) and value:
        latest = value[-1]
        if isinstance(latest, dict):
            return latest.get('value', latest)
        return latest
    if isinstance(value, dict):
        return value.get('value', value)
    return value


def list_countries() -> pd.DataFrame:
    """List all countries in IPU database.

    Returns DataFrame with: iso2, iso3, country_name, parliament_count.
    """
    data = _ipu_get("/countries", {'page[size]': 200})
    rows = []
    for item in data.get('data', []):
        attrs = item['attributes']
        rows.append({
            'iso2': _parse_time_series(attrs.get('country_code')),
            'iso3': _parse_time_series(attrs.get('iso_alpha3')),
            'country_name': _parse_time_series(attrs.get('official_name', attrs.get('country_name'))),
        })
    return pd.DataFrame(rows)


def get_chambers(iso2: str) -> pd.DataFrame:
    """Get parliamentary chambers for a country.

    Args:
        iso2: ISO 3166-1 alpha-2 code (e.g. 'JP', 'US').

    Returns DataFrame with: chamber_id, chamber_name, chamber_type,
    total_seats, men_seats, women_seats, last_election_date, designation_mode,
    electoral_system, term_years.
    """
    data = _ipu_get("/chambers")
    rows = []
    for item in data.get('data', []):
        # ISO2 code is embedded in chamber ID: e.g. 'JP-LC01'
        chamber_iso2 = item['id'].split('-')[0] if '-' in item['id'] else ''
        if chamber_iso2 != iso2:
            continue
        attrs = item['attributes']

        # Chamber name
        name_list = attrs.get('chamber_name', [{}])
        name = name_list[-1].get('value', {}).get('en', '') if name_list else ''

        # Chamber type
        ctype_list = attrs.get('chamber_type', [{}])
        ctype_term = ctype_list[-1].get('term', '') if ctype_list else ''
        chamber_type = CHAMBER_TYPE_MAP.get(ctype_term, ctype_term)

        # Seats
        total_seats = _parse_time_series(attrs.get('current_members_number'))
        men = _parse_time_series(attrs.get('current_men_number'))
        women = _parse_time_series(attrs.get('current_women_number'))

        # Election
        elec_list = attrs.get('date_of_last_election', [])
        last_election = elec_list[-1].get('value', None) if elec_list else None

        # Designation
        desig_list = attrs.get('designation_mode', [{}])
        designation = desig_list[-1].get('term', '') if desig_list else ''

        # Electoral system
        elec_sys_list = attrs.get('electoral_system', [{}])
        electoral_system = elec_sys_list[-1].get('term', '') if elec_sys_list else ''

        # Term
        term = _parse_time_series(attrs.get('term_of_office'))

        rows.append({
            'chamber_id': item['id'],
            'chamber_name': name,
            'chamber_type': chamber_type,
            'total_seats': total_seats,
            'men_seats': men,
            'women_seats': women,
            'last_election_date': last_election,
            'designation_mode': designation,
            'electoral_system': electoral_system,
            'term_years': term,
        })

    return pd.DataFrame(rows)


def get_seats_by_party(iso2: str) -> pd.DataFrame:
    """Get current seat distribution by political group for a country.

    Note: IPU v1 API stores political group data at the chamber level
    via the 'political_groups' and 'number_of_seats_per_group' attributes.
    Coverage varies by country — not all countries report real-time seat data.

    Args:
        iso2: ISO 3166-1 alpha-2 code.

    Returns DataFrame with: chamber_id, chamber_name, party_name, seats, total_seats.
    """
    data = _ipu_get("/chambers")
    rows = []
    for item in data.get('data', []):
        # ISO2 code is embedded in chamber ID: e.g. 'JP-LC01'
        chamber_iso2 = item['id'].split('-')[0] if '-' in item['id'] else ''
        if chamber_iso2 != iso2:
            continue
        attrs = item['attributes']

        name_list = attrs.get('chamber_name', [{}])
        chamber_name = name_list[-1].get('value', {}).get('en', '') if name_list else ''

        total_seats = _parse_time_series(attrs.get('current_members_number'))

        # Political groups
        groups = attrs.get('political_groups', [])
        seats_per_group = attrs.get('number_of_seats_per_group', [])

        if groups and seats_per_group and len(groups) == len(seats_per_group):
            for g, s in zip(groups, seats_per_group):
                party_name = g.get('term', '') if isinstance(g, dict) else str(g)
                seats = _parse_time_series(s)
                rows.append({
                    'chamber_id': item['id'],
                    'chamber_name': chamber_name,
                    'party_name': party_name,
                    'seats': seats,
                    'total_seats': total_seats,
                })

    return pd.DataFrame(rows)


def get_sovereign_chambers() -> pd.DataFrame:
    """Get chambers for all 25 sovereign risk countries.

    Returns DataFrame with all columns from get_chambers() plus iso2.
    """
    frames = []
    for iso3, iso2 in SOVEREIGN_COUNTRIES.items():
        df = get_chambers(iso2)
        if not df.empty:
            df['iso3'] = iso3
            df['iso2'] = iso2
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
