"""
IMF Direction of Trade Statistics (DOTS) via DBnomics.

IMF DOTS provides bilateral trade flow data (exports/imports) between
country pairs. Data is accessed through the DBnomics aggregator, which
normalises the IMF SDMX endpoint.

Provider/Dataset: IMF/DOT
Series pattern: {freq}.{iso2}.{flow}.{counterpart_iso2}
  - freq: A (annual), M (monthly), Q (quarterly)
  - flow: TXG_FOB_USD (goods exports FOB, USD), TMG_CIF_USD (goods imports CIF, USD)
  - iso2: 2-letter ISO country code

No API key required.
"""
import pandas as pd


def _fetch_dbnomics(provider: str, dataset: str, series: str | None = None):
    """Lazy-import DBnomics and fetch series."""
    try:
        import dbnomics
        return dbnomics.fetch_series(provider, dataset, series)
    except ImportError:
        print('[IMF_DOT] dbnomics not installed. pip install dbnomics')
        return pd.DataFrame()
    except Exception as e:
        print(f'[IMF_DOT] fetch error: {e}')
        return pd.DataFrame()


def bilateral_trade(reporter_iso2: str, partner_iso2: str,
                    year: int | None = None) -> pd.DataFrame:
    """Bilateral exports from reporter to partner.

    Args:
        reporter_iso2: 2-letter ISO code of the exporting country (e.g. 'US').
        partner_iso2: 2-letter ISO code of the destination country (e.g. 'CN').
        year: Filter to a specific year. If None, returns all available.

    Returns:
        DataFrame with columns: original_period, value (exports in USD).
    """
    series = f"A.{reporter_iso2.upper()}.TXG_FOB_USD.{partner_iso2.upper()}"
    df = _fetch_dbnomics('IMF', 'DOT', series)
    if df.empty:
        return df

    cols = [c for c in df.columns if c in ('original_period', 'period', 'value')]
    result = df[cols].copy()
    if 'period' in result.columns and 'original_period' not in result.columns:
        result = result.rename(columns={'period': 'original_period'})

    if year:
        result = result[result['original_period'].astype(str).str.startswith(str(year))]

    return result.reset_index(drop=True)


def total_exports(iso2: str, year: int | None = None) -> pd.DataFrame:
    """Total goods exports for a country (all destinations).

    Args:
        iso2: 2-letter ISO code (e.g. 'CN').
        year: Filter to a specific year.

    Returns:
        DataFrame with columns: original_period, value.
    """
    series = f"A.{iso2.upper()}.TXG_FOB_USD.W00"
    df = _fetch_dbnomics('IMF', 'DOT', series)
    if df.empty:
        return df

    cols = [c for c in df.columns if c in ('original_period', 'period', 'value')]
    result = df[cols].copy()
    if 'period' in result.columns and 'original_period' not in result.columns:
        result = result.rename(columns={'period': 'original_period'})

    if year:
        result = result[result['original_period'].astype(str).str.startswith(str(year))]

    return result.reset_index(drop=True)


def total_imports(iso2: str, year: int | None = None) -> pd.DataFrame:
    """Total goods imports for a country (all origins).

    Args:
        iso2: 2-letter ISO code (e.g. 'US').
        year: Filter to a specific year.

    Returns:
        DataFrame with columns: original_period, value.
    """
    series = f"A.{iso2.upper()}.TMG_CIF_USD.W00"
    df = _fetch_dbnomics('IMF', 'DOT', series)
    if df.empty:
        return df

    cols = [c for c in df.columns if c in ('original_period', 'period', 'value')]
    result = df[cols].copy()
    if 'period' in result.columns and 'original_period' not in result.columns:
        result = result.rename(columns={'period': 'original_period'})

    if year:
        result = result[result['original_period'].astype(str).str.startswith(str(year))]

    return result.reset_index(drop=True)


def trade_balance_trend(iso2: str, start_year: int | None = None,
                        end_year: int | None = None) -> pd.DataFrame:
    """Trade balance (exports minus imports) time series for a country.

    Returns DataFrame with columns: year, exports, imports, balance.
    """
    exports = total_exports(iso2)
    imports = total_imports(iso2)

    if exports.empty or imports.empty:
        return pd.DataFrame(columns=['year', 'exports', 'imports', 'balance'])

    exports = exports.rename(columns={'value': 'exports'})
    imports = imports.rename(columns={'value': 'imports'})

    merged = pd.merge(exports, imports, on='original_period', how='outer')
    merged['year'] = merged['original_period'].astype(str).str[:4].astype(int)
    merged['balance'] = merged['exports'] - merged['imports']

    result = merged[['year', 'exports', 'imports', 'balance']].copy()

    if start_year:
        result = result[result['year'] >= start_year]
    if end_year:
        result = result[result['year'] <= end_year]

    return result.sort_values('year').reset_index(drop=True)