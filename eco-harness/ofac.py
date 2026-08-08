"""
OFAC Sanctions Harness — SDN (Specially Designated Nationals) and sanctions programs.

OFAC's REST API (sanctionslistservice.ofac.treas.gov) is unstable/returns 404.
This harness uses the reliable SDN Advanced XML endpoint at treasury.gov.

XML size: ~125MB. Uses streaming iterparse to avoid memory issues.

Data used by C10 (QEGRS geopolitical risk) — sanction_pressure dimension.
"""
import xml.etree.ElementTree as ET
from io import BytesIO
from collections import defaultdict

import pandas as pd
import requests

SDN_XML_URL = "https://www.treasury.gov/ofac/downloads/sdn.xml"

# Programs relevant to sovereign risk assessment
RELEVANT_PROGRAMS = {
    'RUSSIA-EO14024', 'UKRAINE-EO13660', 'UKRAINE-EO13661', 'UKRAINE-EO13662',
    'BELARUS', 'BELARUS-EO14038',
    'IRAN', 'IRAN-EO13599', 'IRGC',
    'DPRK', 'DPRK2', 'DPRK3', 'DPRK4',
    'SYRIA', 'VENEZUELA', 'VENEZUELA-EO13850',
    'CUBA', 'BURMA', 'BURMA-EO14014',
    'MAGNITSKY', 'GLOMAG',
    'COUNTER-TERRORISM', 'SDGT', 'FTO',
    'NON-PROLIFERATION', 'ILLICIT-DRUGS-TRAFFICKING',
    'TRANSNATIONAL-CRIMINAL',
    'CYBER2', 'HOSTAGES-EO14078',
    'CHINA-MILITARY', 'HONG-KONG-EO13936', 'XINJIANG-EO',
    'CAATSA', 'COUNTER-NARCOTICS',
    'BALKANS', 'LIBERIA', 'SOMALIA', 'SUDAN', 'DARFUR',
    'YEMEN', 'LEBANON', 'LIBYA',
    'SOUTH-SUDAN', 'CENTRAL-AFRICAN-REPUBLIC',
    'ETHIOPIA', 'HAITI', 'BURUNDI', 'MALI', 'ZIMBABWE',
    'AFGHANISTAN', 'WMD',
}


def _iterparse_sdn(xml_bytes: bytes, max_entries: int = None):
    """Stream-parse SDN XML and yield entity dicts."""
    ns = '{https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML}'
    context = ET.iterparse(BytesIO(xml_bytes), events=('end',))
    count = 0

    for event, elem in context:
        tag = elem.tag.replace(ns, '')
        if tag not in ('sdnEntry', 'publshInformation'):
            continue

        if tag == 'sdnEntry':
            count += 1
            # Extract entity data
            entry = {
                'uid': elem.findtext(f'{ns}uid', ''),
                'first_name': elem.findtext(f'{ns}firstName', ''),
                'last_name': elem.findtext(f'{ns}lastName', ''),
                'sdn_type': elem.findtext(f'{ns}sdnType', ''),
            }

            # Full name
            full_name_parts = []
            if entry['last_name']:
                full_name_parts.append(entry['last_name'])
            if entry['first_name']:
                full_name_parts.append(entry['first_name'])
            entry['full_name'] = ', '.join(full_name_parts) if full_name_parts else elem.findtext(f'{ns}name', '')

            # Programs
            programs = []
            prog_elem = elem.find(f'{ns}programList')
            if prog_elem is not None:
                for p in prog_elem.findall(f'{ns}program'):
                    programs.append(p.text or '')
            entry['programs'] = '; '.join(programs)

            # Countries from addresses
            countries = set()
            addr_elem = elem.find(f'{ns}addressList')
            if addr_elem is not None:
                for a in addr_elem.findall(f'{ns}address'):
                    country = a.findtext(f'{ns}country', '')
                    if country:
                        countries.add(country)
            entry['countries'] = '; '.join(sorted(countries))

            # Remarks
            remarks = elem.findtext(f'{ns}remarks', '')
            entry['remarks'] = remarks[:500] if remarks else ''

            yield entry
            elem.clear()

            if max_entries and count >= max_entries:
                break

        elif tag == 'publshInformation':
            elem.clear()

    # Clean up remaining
    context = None  # trigger final garbage collection


def fetch_sdn(max_entries: int = None) -> pd.DataFrame:
    """Download and parse SDN Advanced XML.

    Args:
        max_entries: Limit entries for testing. None = full list (~15K entries).

    Returns DataFrame with: uid, full_name, first_name, last_name, sdn_type,
    programs, countries, remarks.
    """
    resp = requests.get(SDN_XML_URL, timeout=120, stream=True)
    resp.raise_for_status()

    # Read in chunks to handle 125MB
    chunks = []
    for chunk in resp.iter_content(chunk_size=8 * 1024 * 1024):
        chunks.append(chunk)
    xml_bytes = b''.join(chunks)

    rows = list(_iterparse_sdn(xml_bytes, max_entries=max_entries))
    return pd.DataFrame(rows)


def get_sanctions_by_program() -> pd.DataFrame:
    """Count entities per sanctions program.

    Returns DataFrame with: program, entity_count, sdn_types.
    """
    df = fetch_sdn()
    if df.empty:
        return pd.DataFrame(columns=['program', 'entity_count', 'sdn_types'])

    program_counts = defaultdict(lambda: {'count': 0, 'types': set()})
    for _, row in df.iterrows():
        if not row['programs']:
            continue
        for prog in row['programs'].split('; '):
            prog = prog.strip()
            if not prog:
                continue
            program_counts[prog]['count'] += 1
            program_counts[prog]['types'].add(row['sdn_type'])

    rows = [{'program': p, 'entity_count': v['count'],
             'sdn_types': ', '.join(sorted(v['types']))}
            for p, v in sorted(program_counts.items(), key=lambda x: -x[1]['count'])]
    return pd.DataFrame(rows)


def get_sanctions_by_country() -> pd.DataFrame:
    """Count sanctioned entities per country (from address data).

    Returns DataFrame with: country, entity_count.
    """
    df = fetch_sdn()
    if df.empty:
        return pd.DataFrame(columns=['country', 'entity_count'])

    country_counts = defaultdict(int)
    for _, row in df.iterrows():
        if not row['countries']:
            continue
        for c in row['countries'].split('; '):
            c = c.strip()
            if c:
                country_counts[c] += 1

    rows = [{'country': c, 'entity_count': n}
            for c, n in sorted(country_counts.items(), key=lambda x: -x[1])]
    return pd.DataFrame(rows)


def get_program_sanctions(program: str) -> pd.DataFrame:
    """Get entities sanctioned under a specific program.

    Args:
        program: Program name (e.g. 'RUSSIA-EO14024', 'IRAN').

    Returns DataFrame with entity details for matching entries.
    """
    df = fetch_sdn()
    if df.empty:
        return df
    mask = df['programs'].str.contains(program, case=False, na=False)
    return df[mask].reset_index(drop=True)


def get_relevant_sanctions() -> pd.DataFrame:
    """Get entities under programs relevant to sovereign risk assessment.

    Filters to programs in RELEVANT_PROGRAMS set above.

    Returns DataFrame limited to entities in geopolitically significant programs.
    """
    df = fetch_sdn()
    if df.empty:
        return df

    def _is_relevant(programs_str):
        if not programs_str:
            return False
        for prog in programs_str.split('; '):
            if prog.strip() in RELEVANT_PROGRAMS:
                return True
        return False

    mask = df['programs'].apply(_is_relevant)
    return df[mask].reset_index(drop=True)


def count_sanctioned_countries() -> dict:
    """Quick count: how many sanctioned entities per sovereign-risk country.

    Maps entity addresses to our 25 sovereign countries and returns
    {iso3: entity_count} for use in C10 sanction_pressure scoring.
    """
    # Map OFAC country names to ISO3
    COUNTRY_MAP = {
        'United States': 'USA', 'United Kingdom': 'GBR', 'Japan': 'JPN',
        'Germany': 'DEU', 'France': 'FRA', 'Italy': 'ITA', 'Canada': 'CAN',
        'Australia': 'AUS', 'South Korea': 'KOR', 'Spain': 'ESP',
        'Netherlands': 'NLD', 'Switzerland': 'CHE', 'Sweden': 'SWE',
        'Belgium': 'BEL', 'Austria': 'AUT',
        'China': 'CHN', 'India': 'IND', 'Brazil': 'BRA', 'Mexico': 'MEX',
        'Indonesia': 'IDN', 'Turkey': 'TUR', 'South Africa': 'ZAF',
        'Russia': 'RUS', 'Saudi Arabia': 'SAU', 'Argentina': 'ARG',
        # Common variants
        'Korea, South': 'KOR', 'Korea, North': 'PRK',
        'Iran, Islamic Republic of': 'IRN', 'Syrian Arab Republic': 'SYR',
        'Venezuela, Bolivarian Republic of': 'VEN',
        'Russian Federation': 'RUS',
        'Taiwan': 'TWN', 'Hong Kong': 'HKG',
        'Burma': 'MMR', 'Myanmar': 'MMR',
        'Czech Republic': 'CZE', 'Slovakia': 'SVK',
        'United Arab Emirates': 'ARE',
    }

    df = get_relevant_sanctions()
    if df.empty:
        return {}

    counts = defaultdict(int)
    for _, row in df.iterrows():
        if not row['countries']:
            continue
        for c in row['countries'].split('; '):
            iso3 = COUNTRY_MAP.get(c.strip())
            if iso3:
                counts[iso3] += 1

    return dict(counts)
