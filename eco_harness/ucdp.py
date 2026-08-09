"""
UCDP Conflict Data Harness — GED API v26.1 for sovereign conflict assessment.

Primary: UCDP GED API v26.1 (ucdpapi.pcr.uu.se) — x-ucdp-access-token header.
Data: 417,968+ georeferenced armed conflict events, 1989–present.

Key endpoints:
  - /api/gedevents/26.1 — latest GED events (3 violence types)
  - Filters: Country (G&W code), StartDate, EndDate, TypeOfViolence, pagesize, page

Coverage (25 C22 countries, 2015-2025):
  5 countries with active conflict: MEX, BRA, IND, PHL, TUR
  20 countries have zero UCDP-level armed conflict on territory

UCDP uses Gleditsch & Ward (G&W) numeric country codes (not ISO3).
Mapping table validated 2026-06-22 — all 25 codes confirmed via API.
"""

import json
import os
import time
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd
import requests

# ── API Config ──────────────────────────────────────────────────────────
API_BASE = "https://ucdpapi.pcr.uu.se/api/gedevents/26.1"
TODAY = date.today().strftime('%Y-%m-%d')

# ── Gleditsch & Ward → ISO3 mapping (25 C22 countries) ─────────────────
GW_TO_ISO3 = {
    2:   'USA',     # United States
    20:  'CAN',     # Canada
    70:  'MEX',     # Mexico
    135: 'PER',     # Peru
    140: 'BRA',     # Brazil
    155: 'CHL',     # Chile
    200: 'GBR',     # United Kingdom
    220: 'FRA',     # France
    255: 'DEU',     # Germany (post-1990)
    325: 'ITA',     # Italy
    560: 'ZAF',     # South Africa
    640: 'TUR',     # Turkey
    670: 'SAU',     # Saudi Arabia
    694: 'QAT',     # Qatar
    696: 'ARE',     # United Arab Emirates
    710: 'CHN',     # China
    732: 'KOR',     # South Korea
    740: 'JPN',     # Japan
    750: 'IND',     # India
    816: 'VNM',     # Vietnam
    820: 'MYS',     # Malaysia
    830: 'SGP',     # Singapore
    840: 'PHL',     # Philippines
    850: 'IDN',     # Indonesia
    900: 'AUS',     # Australia
}

ISO3_TO_GW = {v: k for k, v in GW_TO_ISO3.items()}

TYPE_NAMES = {1: 'state-based', 2: 'non-state', 3: 'one-sided'}


class UCDPHarness:
    """UCDP GED API v26.1 — conflict event extraction + absence scoring.

    Usage:
        ucdp = UCDPHarness(api_token='your_ucdp_token')
        df = ucdp.battle_deaths_annual()          # C22-ready annual panel
        df = ucdp.conflict_absence_index()        # 0-100 sovereign risk score
    """

    def __init__(self, api_token: str = ''):
        self._token = api_token or os.environ.get('UCDP_API_TOKEN', '')
        self._headers = {'x-ucdp-access-token': self._token}

    # ── API connectivity ─────────────────────────────────────────────

    @property
    def is_available(self) -> bool:
        if not self._token:
            return False
        try:
            resp = requests.get(API_BASE, headers=self._headers,
                              params={'pagesize': 1}, timeout=15)
            return resp.status_code == 200
        except Exception:
            return False

    # ── Raw GED events ───────────────────────────────────────────────

    def fetch_ged_events(self, iso3: str, year_start: int = 2015,
                         year_end: int = 2025) -> pd.DataFrame:
        """Fetch all GED events for a country across a year range.

        Returns DataFrame with: id, year, type_of_violence, conflict_name,
        dyad_name, side_a, side_b, latitude, longitude, best, low, high,
        deaths_civilians, date_start, date_end, country, region, etc.
        """
        gw_code = ISO3_TO_GW.get(iso3)
        if gw_code is None:
            print(f'  [UCDP] {iso3}: not in G&W mapping')
            return pd.DataFrame()

        events = self._fetch_paginated(gw_code, year_start, year_end)
        if not events:
            return pd.DataFrame()

        df = pd.DataFrame(events)
        df['iso3'] = iso3
        df['violence_type'] = df['type_of_violence'].map(TYPE_NAMES)
        return df

    def _fetch_paginated(self, gw_code: int, year_start: int,
                         year_end: int) -> list[dict]:
        """Paginate through UCDP API for a single country."""
        all_events = []
        page = 1

        params = {
            'Country': gw_code,
            'StartDate': f'{year_start}-01-01',
            'EndDate': f'{year_end}-12-31',
            'pagesize': 1000,
        }

        while True:
            params['page'] = page
            try:
                resp = requests.get(API_BASE, headers=self._headers,
                                  params=params, timeout=60)
                if resp.status_code == 429:
                    time.sleep(3)
                    continue
                resp.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f'  [UCDP] GW={gw_code}: page {page} error — {e}')
                break

            data = resp.json()
            events = data.get('Result', [])
            all_events.extend(events)

            total_pages = data.get('TotalPages', 0)
            if page >= total_pages or not events:
                break
            page += 1

        return all_events

    # ── Annual battle deaths (C22-ready) ─────────────────────────────

    def battle_deaths_annual(self, iso3_list: Optional[list[str]] = None,
                             year_start: int = 2015, year_end: int = 2025
                             ) -> pd.DataFrame:
        """Pull annual battle deaths for target countries.

        Returns DataFrame: iso3, year, battle_deaths_best, battle_deaths_low,
        battle_deaths_high, conflict_events

        Zero-fills countries with no UCDP events (20/25 C22 countries).
        """
        if iso3_list is None:
            iso3_list = sorted(ISO3_TO_GW.keys())

        if not self._token:
            print('[UCDP] No API token — returning zero-filled panel')
            return self._zero_panel(iso3_list, year_start, year_end)

        all_rows = []
        for iso3 in iso3_list:
            events = self._fetch_paginated(
                ISO3_TO_GW[iso3], year_start, year_end)

            if not events:
                for yr in range(year_start, year_end + 1):
                    all_rows.append({
                        'iso3': iso3, 'year': yr,
                        'battle_deaths_best': 0, 'battle_deaths_low': 0,
                        'battle_deaths_high': 0, 'conflict_events': 0,
                    })
                continue

            agg = {}
            for ev in events:
                yr = ev.get('year')
                if yr is None:
                    continue
                if yr not in agg:
                    agg[yr] = {'best': 0, 'low': 0, 'high': 0, 'events': 0}
                agg[yr]['best'] += (ev.get('best') or 0)
                agg[yr]['low'] += (ev.get('low') or 0)
                agg[yr]['high'] += (ev.get('high') or 0)
                agg[yr]['events'] += 1

            for yr in range(year_start, year_end + 1):
                vals = agg.get(yr, {'best': 0, 'low': 0, 'high': 0, 'events': 0})
                all_rows.append({
                    'iso3': iso3, 'year': yr,
                    'battle_deaths_best': vals['best'],
                    'battle_deaths_low': vals['low'],
                    'battle_deaths_high': vals['high'],
                    'conflict_events': vals['events'],
                })

        return pd.DataFrame(all_rows).sort_values(['iso3', 'year']).reset_index(drop=True)

    def _zero_panel(self, iso3_list, year_start, year_end) -> pd.DataFrame:
        rows = []
        for iso3 in iso3_list:
            for yr in range(year_start, year_end + 1):
                rows.append({
                    'iso3': iso3, 'year': yr,
                    'battle_deaths_best': 0, 'battle_deaths_low': 0,
                    'battle_deaths_high': 0, 'conflict_events': 0,
                })
        return pd.DataFrame(rows)

    # ── Conflict absence index (0-100 sovereign risk score) ──────────

    def conflict_absence_index(self, iso3_list: Optional[list[str]] = None
                               ) -> pd.DataFrame:
        """Score conflict absence 0-100 per country.

        100 = no armed conflict (perfect peace)
        0   = full-scale war

        Uses real UCDP API data when token available; falls back to heuristic.
        """
        if iso3_list is None:
            iso3_list = sorted(ISO3_TO_GW.keys())

        if self.is_available:
            deaths_df = self.battle_deaths_annual(iso3_list)
            return self._score_from_api(deaths_df)

        return self._score_heuristic(iso3_list)

    def _score_from_api(self, deaths_df: pd.DataFrame) -> pd.DataFrame:
        """Score conflict absence from real UCDP battle death data."""
        rows = []
        for iso3, grp in deaths_df.groupby('iso3'):
            total_deaths = grp['battle_deaths_best'].sum()
            max_annual = grp['battle_deaths_best'].max()
            active_years = (grp['battle_deaths_best'] > 0).sum()
            total_events = grp['conflict_events'].sum()

            # Intensity classification from actual data
            if max_annual >= 1000 or total_deaths >= 5000:
                intensity = 'war'
            elif max_annual >= 25:
                intensity = 'minor'
            else:
                intensity = 'none'

            score = _score_conflict_absence(intensity, max_annual, active_years)

            rows.append({
                'iso3': iso3,
                'conflict_absence_index': score,
                'intensity': intensity,
                'battle_deaths_est': int(total_deaths),
                'active_conflicts': active_years,
                'conflict_events': int(total_events),
                'max_annual_deaths': int(max_annual),
                'data_source': 'ucdp_api_v26.1',
                'as_of_date': TODAY,
            })

        return pd.DataFrame(rows)

    def _score_heuristic(self, iso3_list) -> pd.DataFrame:
        """Heuristic scoring when API unavailable (kept as fallback)."""
        print('[UCDP] API unavailable — using heuristic baseline')
        rows = []
        for iso3 in iso3_list:
            info = _HEURISTIC_BASELINE.get(iso3, {})
            score = _score_conflict_absence(
                info.get('intensity', 'none'),
                info.get('battle_deaths', 0),
                info.get('active_conflicts', 0),
            )
            rows.append({
                'iso3': iso3,
                'conflict_absence_index': score,
                'intensity': info.get('intensity', 'none'),
                'battle_deaths_est': info.get('battle_deaths', 0),
                'active_conflicts': info.get('active_conflicts', 0),
                'note': info.get('note', ''),
                'data_source': 'heuristic_baseline',
                'as_of_date': TODAY,
            })
        return pd.DataFrame(rows)


# ── Scoring logic ──────────────────────────────────────────────────────

def _score_conflict_absence(intensity: str, battle_deaths: int,
                            active_years: int) -> float:
    """Score conflict absence 0-100.

    100 = no conflict, 0 = full-scale war.
    """
    if intensity == 'war':
        base = 5
    elif intensity == 'minor':
        if battle_deaths >= 5000:
            base = 10
        elif battle_deaths >= 1000:
            base = 25
        elif battle_deaths >= 100:
            base = 45
        else:
            base = 60
    else:
        base = 95

    penalty = (active_years - 1) * 8 if active_years > 1 else 0
    return float(max(0, min(100, base - penalty)))


# ── Heuristic baseline (fallback when API unavailable) ─────────────────

_HEURISTIC_BASELINE = {
    'ARE': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'No armed conflict on territory'},
    'AUS': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'No armed conflict'},
    'BRA': {'active_conflicts': 1, 'intensity': 'minor',   'battle_deaths': 10338, 'note': 'Drug gang/government clashes, Amazon land conflicts'},
    'CAN': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'No armed conflict'},
    'CHL': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'Mapuche disputes below UCDP 25-death threshold'},
    'CHN': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'Border standoffs below UCDP threshold'},
    'DEU': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'No armed conflict'},
    'FRA': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'Domestic terror only; no UCDP-level conflict on territory'},
    'GBR': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'No armed conflict on territory'},
    'IDN': {'active_conflicts': 1, 'intensity': 'minor',   'battle_deaths': 50,  'note': 'West Papua insurgency (low-level)'},
    'IND': {'active_conflicts': 4, 'intensity': 'minor',   'battle_deaths': 5172, 'note': 'Kashmir + India-Pakistan border + Naxalite + Manipur'},
    'ITA': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'No armed conflict'},
    'JPN': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'No armed conflict'},
    'KOR': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'DMZ incidents below UCDP 25-death threshold'},
    'MEX': {'active_conflicts': 1, 'intensity': 'war',     'battle_deaths': 93058, 'note': 'Drug cartel violence (CJNG, Sinaloa). ~93058 deaths 2017-2025'},
    'MYS': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'No armed conflict'},
    'PER': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'Shining Path remnants below UCDP threshold'},
    'PHL': {'active_conflicts': 2, 'intensity': 'minor',   'battle_deaths': 1342, 'note': 'Mindanao: NPA + MILF/BIFF + Abu Sayyaf'},
    'QAT': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'No armed conflict'},
    'SAU': {'active_conflicts': 1, 'intensity': 'minor',   'battle_deaths': 200, 'note': 'Yemen border operations, Houthi missile/drone attacks'},
    'SGP': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'No armed conflict'},
    'TUR': {'active_conflicts': 2, 'intensity': 'minor',   'battle_deaths': 364,  'note': 'PKK insurgency + Syria cross-border operations'},
    'USA': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'No armed conflict on territory'},
    'VNM': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'No armed conflict'},
    'ZAF': {'active_conflicts': 0, 'intensity': 'none',    'battle_deaths': 0,   'note': 'High violent crime (non-political, not UCDP-classified)'},
}


# ── Module-level convenience ───────────────────────────────────────────
# Backward-compatible with callers that use ucdp.get_conflict_absence_index()

def get_conflict_absence_index() -> pd.DataFrame:
    """Convenience: get conflict_absence_index via default UCDPHarness."""
    ucdp = UCDPHarness()
    return ucdp.conflict_absence_index()
