"""
ComtradeHarness — UN Comtrade international trade data API.

UN Comtrade provides detailed bilateral trade flow data (exports/imports)
between countries, classified by HS commodity codes.

API: https://comtradeapi.un.org/data/v1/
Auth: Subscription key (free registration at comtradeplus.un.org)
Env: UNCOMTRADE_API_KEY

Rate limit: ~500 requests/day on free tier. Built-in 0.5s delay between calls.
"""
import os
import time

import pandas as pd
import requests

COMTRADE_BASE = 'https://comtradeapi.un.org/data/v1'

# ISO3 to UN M49 numeric codes for the 25 sovereign countries
_ISO3_TO_M49 = {
    'ARE': 784, 'AUS': 36,  'BRA': 76,  'CAN': 124, 'CHL': 152,
    'CHN': 156, 'DEU': 276, 'FRA': 251, 'GBR': 826, 'IDN': 360,
    'IND': 356, 'ITA': 380, 'JPN': 392, 'KOR': 410, 'MEX': 484,
    'MYS': 458, 'PER': 604, 'PHL': 608, 'QAT': 634, 'SAU': 682,
    'SGP': 702, 'TUR': 792, 'USA': 842, 'VNM': 704, 'ZAF': 710,
}


class ComtradeHarness:
    """UN Comtrade trade data access."""

    def __init__(self, api_key: str = ''):
        self._key = api_key or os.environ.get('UNCOMTRADE_API_KEY', '')
        if not self._key:
            print('[Comtrade] No API key — set UNCOMTRADE_API_KEY env var.'
                  ' Register: https://comtradeplus.un.org/')

    def _headers(self) -> dict:
        return {
            'Ocp-Apim-Subscription-Key': self._key,
            'Accept': 'application/json',
        }

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """GET request with rate limit and error handling."""
        if not self._key:
            return {}
        url = f'{COMTRADE_BASE}/{endpoint}'
        try:
            resp = requests.get(url, headers=self._headers(),
                                params=params or {}, timeout=30)
            if resp.status_code == 429:
                time.sleep(5)
                resp = requests.get(url, headers=self._headers(),
                                    params=params or {}, timeout=30)
            resp.raise_for_status()
            time.sleep(0.6)  # free-tier rate limit
            return resp.json()
        except Exception as e:
            print(f'[Comtrade] request error: {e}')
            return {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def trade_flow(self, reporter: str, partner: str = 'ALL',
                   commodity_code: str = 'TOTAL', year: int = 2024,
                   flow: str = 'X') -> pd.DataFrame:
        """Basic trade flow lookup.

        Args:
            reporter: ISO3 of the reporting country.
            partner: ISO3 of the partner country, or 'ALL' for world total.
            commodity_code: HS code or 'TOTAL' for all commodities.
            year: Reporting year.
            flow: 'X' for exports, 'M' for imports.

        Returns:
            DataFrame with trade value and metadata.
        """
        reporter_m49 = _ISO3_TO_M49.get(reporter.upper())
        if reporter_m49 is None:
            print(f'[Comtrade] unknown country: {reporter}')
            return pd.DataFrame()

        partner_m49 = _ISO3_TO_M49.get(partner.upper()) if partner != 'ALL' else 0

        params = {
            'reporterCode': reporter_m49,
            'period': str(year),
            'flowCode': flow,
            'cmdCode': commodity_code,
        }
        if partner_m49:
            params['partnerCode'] = partner_m49

        data = self._get('get/C/A/HS', params)
        if not data.get('data'):
            return pd.DataFrame()

        rows = []
        for item in data['data']:
            rows.append({
                'reporter': reporter.upper(),
                'partner': partner.upper() if partner != 'ALL' else 'WLD',
                'year': year,
                'flow': 'export' if flow == 'X' else 'import',
                'commodity': commodity_code,
                'value_usd': item.get('primaryValue', 0),
            })
        return pd.DataFrame(rows)

    def bilateral_trade(self, reporter: str, partner: str,
                        year: int = 2024) -> pd.DataFrame:
        """Two-way trade between two countries (exports + imports).

        Returns DataFrame with: reporter, partner, year, exports, imports, balance.
        """
        exports = self.trade_flow(reporter, partner, year=year, flow='X')
        imports = self.trade_flow(reporter, partner, year=year, flow='M')

        exp_val = float(exports['value_usd'].sum()) if not exports.empty else 0.0
        imp_val = float(imports['value_usd'].sum()) if not imports.empty else 0.0

        return pd.DataFrame([{
            'reporter': reporter.upper(),
            'partner': partner.upper(),
            'year': year,
            'exports_usd': exp_val,
            'imports_usd': imp_val,
            'balance_usd': exp_val - imp_val,
        }])

    def total_trade(self, reporter: str, year: int = 2024) -> pd.DataFrame:
        """Total exports and imports for a country in a given year.

        Returns DataFrame with: reporter, year, exports_usd, imports_usd, balance_usd.
        """
        exports = self.trade_flow(reporter, partner='ALL', year=year, flow='X')
        imports = self.trade_flow(reporter, partner='ALL', year=year, flow='M')

        exp_val = float(exports['value_usd'].sum()) if not exports.empty else 0.0
        imp_val = float(imports['value_usd'].sum()) if not imports.empty else 0.0

        return pd.DataFrame([{
            'reporter': reporter.upper(),
            'year': year,
            'exports_usd': exp_val,
            'imports_usd': imp_val,
            'balance_usd': exp_val - imp_val,
        }])

    def top_partners(self, reporter: str, year: int = 2024,
                     n: int = 10, flow: str = 'X') -> pd.DataFrame:
        """Top N trading partners by export or import value.

        Args:
            reporter: ISO3 reporting country.
            year: Reporting year.
            n: Number of top partners to return.
            flow: 'X' (exports) or 'M' (imports).

        Returns:
            DataFrame with: partner_iso3, value_usd.
        """
        reporter_m49 = _ISO3_TO_M49.get(reporter.upper())
        if reporter_m49 is None:
            print(f'[Comtrade] unknown country: {reporter}')
            return pd.DataFrame()

        params = {
            'reporterCode': reporter_m49,
            'period': str(year),
            'flowCode': flow,
            'cmdCode': 'TOTAL',
        }
        data = self._get('get/C/A/HS', params)
        if not data.get('data'):
            return pd.DataFrame()

        # Aggregate by partner
        partner_vals: dict[str, float] = {}
        for item in data['data']:
            pc = item.get('partnerCode', 0)
            partner_vals[str(pc)] = partner_vals.get(str(pc), 0) + item.get('primaryValue', 0)

        sorted_items = sorted(partner_vals.items(), key=lambda x: x[1], reverse=True)[:n]

        # Reverse-lookup M49 → ISO3
        m49_to_iso3 = {str(v): k for k, v in _ISO3_TO_M49.items()}
        m49_to_iso3['0'] = 'WLD'

        rows = [{'partner_iso3': m49_to_iso3.get(code, code),
                 'value_usd': val} for code, val in sorted_items]
        return pd.DataFrame(rows)

    def trade_balance_trend(self, reporter: str, start_year: int = 2015,
                            end_year: int = 2024) -> pd.DataFrame:
        """Trade balance (exports - imports) time series for a country.

        Returns DataFrame with: year, exports_usd, imports_usd, balance_usd.
        """
        rows = []
        for y in range(start_year, end_year + 1):
            rec = self.total_trade(reporter, year=y)
            if rec.empty:
                continue
            rows.append(rec.iloc[0].to_dict())
        return pd.DataFrame(rows)
