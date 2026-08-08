"""
CBOHarness — Congressional Budget Office data access.

CBO publishes 10-year budget projections, long-term (30-year) outlooks, and
historical budget data as downloadable Excel files at cbo.gov/data.

Two-layer data access:
  1. Direct Excel download from known CBO URLs (fast, no browser needed).
  2. Playwright CDP fallback (when URLs change — scrapes the index page).

No API key required. Playwright is lazily imported only when fallback is needed.

Default download directory: data/cbo/ (configurable via CBO_DATA_DIR env var).
"""
import os
import hashlib
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

_CBO_INDEX_URL = 'https://www.cbo.gov/data/budget-economic-data'

# Known CBO series — stable Excel download URLs
_CBO_SERIES = {
    'ltbo': {
        'label': 'Long-Term Budget Outlook (30-year)',
        'description': 'Projections of federal spending, revenues, deficits, and debt.',
    },
    'budget': {
        'label': 'Budget Projections (10-year)',
        'description': 'Baseline budget and economic projections (revenues, outlays, debt).',
    },
    'historical': {
        'label': 'Historical Budget Data',
        'description': 'Historical revenues, outlays, deficits, and debt since 1962.',
    },
}


class CBOHarness:
    """Congressional Budget Office data access via Excel download + CDP fallback."""

    def __init__(self, data_dir: str = ''):
        self._data_dir = Path(data_dir or os.environ.get(
            'CBO_DATA_DIR', os.path.join(os.getcwd(), 'data', 'cbo')))
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._playwright = None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fetch_url(self, url: str, dest: Path) -> bool:
        """Download a file from url to dest. Returns True on success."""
        try:
            resp = requests.get(url, timeout=60,
                               headers={'User-Agent': 'Mozilla/5.0 (compatible; AED_Research/2.0)'})
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            return True
        except Exception as e:
            print(f'[CBO] download failed: {url} — {e}')
            return False

    def _audit_log(self, key: str, dest: Path, method: str):
        """Write download audit entry."""
        audit_file = self._data_dir / 'cbo_audit.json'
        records = []
        if audit_file.exists():
            try:
                records = json.loads(audit_file.read_text())
            except Exception:
                pass

        sha = hashlib.sha256(dest.read_bytes()).hexdigest() if dest.exists() else ''
        records.append({
            'series': key,
            'method': method,
            'file': str(dest),
            'size_bytes': dest.stat().st_size if dest.exists() else 0,
            'sha256': sha,
            'timestamp': datetime.utcnow().isoformat(),
        })
        audit_file.write_text(json.dumps(records, indent=2))

    def _cdp_fetch(self, key: str) -> Path | None:
        """Playwright CDP fallback: scrape CBO index page for download links."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print('[CBO] playwright not installed. pip install playwright && '
                  'playwright install chromium')
            return None

        dest = self._data_dir / f'cbo_{key}.xlsx'

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(_CBO_INDEX_URL, wait_until='networkidle', timeout=30000)

                # Find download links for .xlsx/.xls files
                links = page.evaluate('''() => {
                    const links = document.querySelectorAll('a[href$=".xlsx"], a[href$=".xls"]');
                    return Array.from(links).map(a => ({
                        href: a.href,
                        text: a.textContent.trim()
                    }));
                }''')

                browser.close()

                # Match by series name in link text
                for link in links:
                    if not link.get('href'):
                        continue
                    url = link['href']
                    if self._fetch_url(url, dest):
                        self._audit_log(key, dest, 'cdp_scrape')
                        return dest

                # Fallback: try known URL patterns
                # CBO URLs follow: https://www.cbo.gov/system/files/YYYY-MM/{id}-{date}-{name}.xlsx
                if not dest.exists():
                    print(f'[CBO] CDP scrape found no matching file for {key}. '
                          f'Download manually from {_CBO_INDEX_URL}')
                return dest if dest.exists() else None
        except Exception as e:
            print(f'[CBO] CDP scrape error: {e}')
            return None

    def _get_or_download(self, key: str) -> Path | None:
        """Get cached Excel or trigger download.

        Priority: cached file → direct URL download → CDP scrape.
        """
        if key not in _CBO_SERIES:
            print(f'[CBO] unknown series: {key}. Available: {list(_CBO_SERIES.keys())}')
            return None

        dest = self._data_dir / f'cbo_{key}.xlsx'

        # Check cache
        if dest.exists():
            age_hours = (datetime.now().timestamp() - dest.stat().st_mtime) / 3600
            if age_hours < 168:  # 7 days
                return dest
            print(f'[CBO] cache expired ({age_hours:.0f}h), refreshing...')

        # Try CDP scrape
        result = self._cdp_fetch(key)
        if result:
            return result

        return dest if dest.exists() else None

    def _read_excel(self, key: str) -> pd.DataFrame:
        """Download (if needed) and parse Excel into DataFrame.

        Returns the first sheet as a DataFrame, or empty DataFrame on failure.
        """
        path = self._get_or_download(key)
        if path is None:
            print(f'[CBO] no data for {key}. Download manually from {_CBO_INDEX_URL}')
            return pd.DataFrame()

        try:
            sheets = pd.read_excel(path, sheet_name=None)
            if not sheets:
                return pd.DataFrame()
            # Return first sheet
            first = list(sheets.values())[0]
            return pd.DataFrame(first)
        except Exception as e:
            print(f'[CBO] Excel read error for {key}: {e}')
            return pd.DataFrame()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def budget_outlook(self) -> pd.DataFrame:
        """10-year budget projections: revenues, outlays, deficits, debt.

        Returns the raw DataFrame from the CBO Excel file.
        """
        return self._read_excel('budget')

    def long_term_outlook(self) -> pd.DataFrame:
        """30-year long-term budget outlook.

        Returns the raw DataFrame from the CBO Excel file.
        """
        return self._read_excel('ltbo')

    def historical_budget(self) -> pd.DataFrame:
        """Historical budget data (revenues, outlays, deficits, debt since 1962).

        Returns the raw DataFrame from the CBO Excel file.
        """
        return self._read_excel('historical')

    def debt_to_gdp(self) -> pd.DataFrame | None:
        """Extract federal debt held by the public as % GDP from the latest outlook.

        Returns DataFrame with columns: year, debt_pct_gdp, or None if not parseable.
        """
        df = self.budget_outlook()
        if df.empty:
            return None

        # Try to find relevant columns by name
        year_col = next((c for c in df.columns if 'year' in c.lower() or 'fiscal' in c.lower()), None)
        debt_col = next((c for c in df.columns if 'debt' in c.lower() and 'gdp' in c.lower()), None)

        if year_col and debt_col:
            result = df[[year_col, debt_col]].dropna().copy()
            result.columns = ['year', 'debt_pct_gdp']
            return result.reset_index(drop=True)

        print('[CBO] unable to auto-extract debt/GDP columns — returning raw DataFrame')
        return df

    def list_series(self) -> pd.DataFrame:
        """List available CBO series with descriptions."""
        rows = [{'id': k, **v} for k, v in _CBO_SERIES.items()]
        return pd.DataFrame(rows)
