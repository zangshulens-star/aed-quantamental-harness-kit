"""
SDMX Harness — OECD + ECB + Eurostat via opensdmx v0.12.1+.

Data limits: SDMX endpoints are public, no key. Rate varies by provider.
opensdmx caches in SQLite+Parquet — first fetch per dataset is slow, replay is instant.

Changes for v0.12.1:
  - fetch() takes dataflow_id (long identifier), not simple dataset name
  - Returns polars DataFrame (converted to pandas for eco_harness consistency)
  - Dimension filters use SDMX names (REF_AREA not 'country')
  - Windows GBK crash patched on import
"""
import sys
import builtins
from functools import lru_cache

# Fix Windows GBK encoding crash in opensdmx v0.12.1
_orig_open = builtins.open
def _utf8_open(file, mode='r', **kwargs):
    if 'b' not in mode and 'encoding' not in kwargs:
        file_str = str(file) if hasattr(file, '__fspath__') else file
        if isinstance(file_str, str):
            if 'json' in file_str or 'opensdmx' in file_str:
                kwargs['encoding'] = 'utf-8'
    return _orig_open(file, mode, **kwargs)
builtins.open = _utf8_open


# Convenience: common SDMX dimension name mappings
DIM_MAP = {
    'country': 'REF_AREA',
    'freq': 'FREQ',
    'frequency': 'FREQ',
    'currency': 'CURRENCY',
    'adjustment': 'ADJUSTMENT',
    'sector': 'SECTOR',
    'transaction': 'TRANSACTION',
    'activity': 'ACTIVITY',
    'expenditure': 'EXPENDITURE',
    'unit': 'UNIT_MEASURE',
}

# Convenience: common dataflow IDs by provider:dataset
KNOWN_DATASETS = {
    'oecd': {
        'QNA': 'OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_USD',
        'QNA_growth': 'OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD',
        'QNA_income': 'OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_INCOME',
        'QNA_output': 'OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_BY_ACTIVITY_OUTPUT',
        'CPI': 'OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL',
        'KEI': 'OECD.SDD.STES,DSD_KEI@DF_KEI,4.0',
        'BOP': 'OECD.SDD.TPS,DSD_BOP@DF_BOP,1.0',
    },
    'ecb': {
        'EXR': 'EXR',
        'YC': 'YC',
    },
    'eurostat': {
        'prc_hicp_manr': 'ESTAT,PRC_HICP_MANR@DF_PRC_HICP_MANR',
    },
}


class SDMXHarness:
    """OECD + ECB + Eurostat unified access via SDMX protocol (opensdmx v0.12.1+)."""

    def __init__(self):
        self._loaded = False
        self._sdmx = None

    def _ensure(self):
        if self._loaded:
            return
        try:
            import opensdmx
            self._sdmx = opensdmx
            self._loaded = True
        except ImportError:
            print('[SDMXHarness] opensdmx not installed — pip install opensdmx')
            raise

    def _fetch(self, dataflow_id: str, **filters):
        """Internal fetch: call opensdmx fetch(), return pandas DataFrame."""
        self._ensure()
        # Map convenience param names to SDMX dimension names
        mapped = {}
        for k, v in filters.items():
            sdmx_key = DIM_MAP.get(k, k)
            mapped[sdmx_key] = v
        result = self._sdmx.fetch(dataflow_id, **mapped)
        return result.to_pandas()

    # --- OECD ---

    def oecd(self, dataset: str = 'QNA', **filters):
        """Fetch OECD dataset.

        Convenience datasets (see KNOWN_DATASETS):
          - QNA: Quarterly GDP & components, expenditure approach, USD
          - QNA_growth: Quarterly real GDP growth, OECD countries
          - QNA_income: GDP income approach
          - QNA_output: GDP output approach by activity
          - CPI: Consumer Price Index

        Args:
            dataset: Short name ('QNA') or full dataflow ID.
            **filters: Dimension filters: country='USA', freq='Q' etc.
        """
        self._ensure()
        self._sdmx.set_provider('oecd')
        df_id = KNOWN_DATASETS.get('oecd', {}).get(dataset, dataset)
        return self._fetch(df_id, **filters)

    # --- ECB ---

    def ecb(self, dataset: str = 'EXR', **filters):
        """Fetch ECB dataset.

        Convenience datasets:
          - EXR: Exchange Rates
          - YC: Yield Curve

        Args:
            dataset: Short name or full dataflow ID.
            **filters: currency='USD', freq='D' etc.
        """
        self._ensure()
        self._sdmx.set_provider('ecb')
        df_id = KNOWN_DATASETS.get('ecb', {}).get(dataset, dataset)
        return self._fetch(df_id, **filters)

    # --- Eurostat ---

    def eurostat(self, dataset: str = 'prc_hicp_manr', **filters):
        """Fetch Eurostat dataset.

        Convenience datasets:
          - prc_hicp_manr: HICP Monthly Annual Rate of Change

        Args:
            dataset: Short name or full dataflow ID.
            **filters: country='DE' etc.
        """
        self._ensure()
        self._sdmx.set_provider('eurostat')
        df_id = KNOWN_DATASETS.get('eurostat', {}).get(dataset, dataset)
        return self._fetch(df_id, **filters)

    # --- Discovery ---

    def search(self, keyword: str, provider: str = 'oecd'):
        """Search datasets in a provider. Returns polars DataFrame of matching dataflows."""
        self._ensure()
        self._sdmx.set_provider(provider)
        return self._sdmx.search_dataset(keyword)

    def list_datasets(self, provider: str = 'oecd'):
        """List all available dataflows for the provider."""
        self._ensure()
        self._sdmx.set_provider(provider)
        return self._sdmx.all_available()
