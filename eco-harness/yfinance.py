"""
YFinanceHarness — Yahoo Finance market data (gold, FX, crude, equities, etc.).

Provides standardised access to daily/monthly price data for commodities,
currencies, stock indices, bitcoin, and volatility indices via the yfinance
library (free, no API key required).

All time-series methods return a DataFrame with columns: date, value.
All methods accept optional start/end dates in 'YYYY-MM-DD' format.
"""
import pandas as pd


# FX pairs: iso3 → (yfinance_ticker, is_inverse)
# is_inverse=True: ticker quotes USD per local (e.g., USDJPY → invert)
# is_inverse=False: ticker quotes local per USD (e.g., EURUSD → direct)
FX_CURRENCY_MAP: dict[str, tuple[str, bool]] = {
    'ARE': ('USDAED=X', True),   'AUS': ('AUDUSD=X', False),
    'BRA': ('USDBRL=X', True),   'CAN': ('USDCAD=X', True),
    'CHL': ('USDCLP=X', True),   'CHN': ('USDCNY=X', True),
    'DEU': ('EURUSD=X', False),  'FRA': ('EURUSD=X', False),
    'GBR': ('GBPUSD=X', False),  'IDN': ('USDIDR=X', True),
    'IND': ('USDINR=X', True),   'ITA': ('EURUSD=X', False),
    'JPN': ('USDJPY=X', True),   'KOR': ('USDKRW=X', True),
    'MEX': ('USDMXN=X', True),   'MYS': ('USDMYR=X', True),
    'PER': ('USDPEN=X', True),   'PHL': ('USDPHP=X', True),
    'QAT': ('USDQAR=X', True),   'SAU': ('USDSAR=X', True),
    'SGP': ('USDSGD=X', True),   'TUR': ('USDTRY=X', True),
    'USA': ('__USD__', False),   'VNM': ('USDVND=X', True),
    'ZAF': ('USDZAR=X', True),
}

# Stock index tickers: iso3 → list of (ticker, label, board)
_STOCK_INDEX_MAP: dict[str, list[tuple[str, str, str]]] = {
    'USA': [('^GSPC', 'S&P 500', 'main'), ('^IXIC', 'NASDAQ', 'second')],
    'CHN': [('000001.SS', 'SSE Composite', 'main'), ('588000.SS', 'STAR 50 ETF', 'second')],
    'JPN': [('^N225', 'Nikkei 225', 'main'), ('1321.T', 'TOPIX ETF', 'second')],
    'KOR': [('^KS11', 'KOSPI', 'main'), ('^KQ11', 'KOSDAQ', 'second')],
    'DEU': [('^GDAXI', 'DAX', 'main'), ('^MDAXI', 'MDAX', 'second')],
    'GBR': [('^FTSE', 'FTSE 100', 'main'), ('^FTMC', 'FTSE 250', 'second')],
    'AUS': [('^AXJO', 'ASX 200', 'main'), ('^AORD', 'All Ordinaries', 'second')],
    'IND': [('^BSESN', 'BSE Sensex', 'main'), ('^CRSLDX', 'Nifty 500', 'second')],
    'BRA': [('^BVSP', 'Ibovespa', 'main'), ('SMAL11.SA', 'Small Cap ETF', 'second')],
    'CAN': [('^GSPTSE', 'S&P/TSX', 'main'), ('XIC.TO', 'iShares S&P/TSX', 'second')],
    'SAU': [('^TASI.SR', 'Tadawul', 'main')],
    'FRA': [('^FCHI', 'CAC 40', 'main')],
    'ITA': [('FTSEMIB.MI', 'FTSE MIB', 'main')],
    'SGP': [('^STI', 'Straits Times', 'main')],
    'MEX': [('^MXX', 'IPC Mexico', 'main')],
    'TUR': [('XU100.IS', 'BIST 100', 'main')],
    'ZAF': [('^JN0U.JO', 'JSE Top 40', 'main')],
    'MYS': [('^KLSE', 'FTSE KLCI', 'main')],
    'IDN': [('^JKSE', 'IDX Composite', 'main')],
    'PHL': [('PSEI.PS', 'PSEi', 'main')],
    'CHL': [('^IPSA', 'IPSA', 'main')],
    'PER': [('^SPBLPGPT', 'S&P/BVL General', 'main')],
    'VNM': [('^VNINDEX', 'VN Index', 'main')],
    'QAT': [('^QSI', 'QE General', 'main')],
    'ARE': [('^ADI', 'ADX General', 'main')],
}


class YFinanceHarness:
    """Yahoo Finance market data — commodities, FX, equities, crypto, vol."""

    def __init__(self):
        self._yf = None

    def _init(self):
        if self._yf is None:
            import yfinance as yf
            self._yf = yf

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_ticker(self, ticker: str, start: str | None = None,
                      end: str | None = None, period: str = '6y') -> pd.DataFrame:
        """Fetch a single ticker's monthly close history.

        Returns DataFrame with columns: date, value.
        """
        self._init()
        try:
            t = self._yf.Ticker(ticker)
            hist = t.history(period=period)
            if hist.empty:
                return pd.DataFrame(columns=['date', 'value'])
            monthly = hist['Close'].resample('ME').last().dropna()
            result = pd.DataFrame({
                'date': monthly.index.strftime('%Y-%m-%d'),
                'value': monthly.values,
            })
            if start:
                result = result[result['date'] >= start]
            if end:
                result = result[result['date'] <= end]
            return result.reset_index(drop=True)
        except Exception as e:
            print(f'[YFinance] ticker {ticker} fetch error: {e}')
            return pd.DataFrame(columns=['date', 'value'])

    # ------------------------------------------------------------------
    # Commodities
    # ------------------------------------------------------------------

    def gold(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """Gold futures price (USD/oz). Ticker: GC=F."""
        return self._fetch_ticker('GC=F', start, end)

    def crude_oil(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """WTI Crude Oil futures (USD/barrel). Ticker: CL=F."""
        return self._fetch_ticker('CL=F', start, end)

    def brent_crude(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """Brent Crude Oil futures (USD/barrel). Ticker: BZ=F."""
        return self._fetch_ticker('BZ=F', start, end)

    def natural_gas(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """Henry Hub Natural Gas futures (USD/MMBtu). Ticker: NG=F."""
        return self._fetch_ticker('NG=F', start, end)

    # ------------------------------------------------------------------
    # Crypto
    # ------------------------------------------------------------------

    def bitcoin(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """Bitcoin price (USD). Ticker: BTC-USD."""
        return self._fetch_ticker('BTC-USD', start, end)

    # ------------------------------------------------------------------
    # Volatility indices
    # ------------------------------------------------------------------

    def vix(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """CBOE Volatility Index (VIX). Ticker: ^VIX."""
        return self._fetch_ticker('^VIX', start, end)

    def move_index(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """ICE BofA MOVE Index (Treasury bond volatility). Ticker: ^MOVE."""
        return self._fetch_ticker('^MOVE', start, end)

    # ------------------------------------------------------------------
    # Equity indices
    # ------------------------------------------------------------------

    def sp500(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """S&P 500 index. Ticker: ^GSPC."""
        return self._fetch_ticker('^GSPC', start, end)

    def nasdaq(self, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """NASDAQ Composite. Ticker: ^IXIC."""
        return self._fetch_ticker('^IXIC', start, end)

    def stock_index(self, iso3: str, board: str = 'main',
                    start: str | None = None, end: str | None = None) -> pd.DataFrame:
        """Stock index for a country by ISO3 code.

        Args:
            iso3: 3-letter ISO country code (e.g. 'USA', 'JPN', 'DEU').
            board: 'main' or 'second'. Returns main index if second not available.
            start/end: Date bounds in 'YYYY-MM-DD' format.

        Returns DataFrame with columns: date, value, or empty if country not found.
        """
        entries = _STOCK_INDEX_MAP.get(iso3.upper(), [])
        if not entries:
            print(f'[YFinance] no stock index mapping for {iso3}')
            return pd.DataFrame(columns=['date', 'value'])

        # Prefer requested board, fall back to first available
        for ticker, label, b in entries:
            if b == board:
                return self._fetch_ticker(ticker, start, end)
        # Fallback to first entry
        return self._fetch_ticker(entries[0][0], start, end)

    def stock_indices_all(self, iso3: str,
                          start: str | None = None, end: str | None = None) -> dict:
        """All available stock indices for a country.

        Returns dict like: {'main': DataFrame, 'second': DataFrame or None}.
        """
        entries = _STOCK_INDEX_MAP.get(iso3.upper(), [])
        result: dict = {}
        for ticker, label, board in entries:
            df = self._fetch_ticker(ticker, start, end)
            result[board] = {'label': label, 'ticker': ticker, 'data': df}
        return result

    def list_countries(self) -> list[str]:
        """List all countries with stock index mappings."""
        return sorted(_STOCK_INDEX_MAP.keys())

    # ------------------------------------------------------------------
    # FX
    # ------------------------------------------------------------------

    def fx_pair(self, iso3: str) -> float | None:
        """Latest FX spot rate: USD per unit of local currency.

        Example: fx_pair('EUR') → 1.14 means 1 EUR = 1.14 USD.
                 fx_pair('JPY') → 0.0067 means 1 JPY = 0.0067 USD.

        Returns None if the ticker fails.
        """
        entry = FX_CURRENCY_MAP.get(iso3.upper())
        if entry is None:
            print(f'[YFinance] no FX mapping for {iso3}')
            return None
        ticker, is_inverse = entry
        if ticker == '__USD__':
            return 1.0

        self._init()
        try:
            t = self._yf.Ticker(ticker)
            hist = t.history(period='5d')
            if hist.empty:
                return None
            rate = float(hist['Close'].iloc[-1])
            return round(1.0 / rate, 8) if is_inverse else round(rate, 8)
        except Exception as e:
            print(f'[YFinance] FX {iso3} ({ticker}) error: {e}')
            return None

    def fx_basket(self, iso3_list: list[str] | None = None) -> pd.DataFrame:
        """Latest FX spot rates for multiple currencies vs USD.

        Returns DataFrame with columns: iso3, rate (USD per unit of local).
        """
        if iso3_list is None:
            iso3_list = list(FX_CURRENCY_MAP.keys())
        rows = []
        for iso3 in iso3_list:
            rate = self.fx_pair(iso3)
            rows.append({'iso3': iso3, 'rate': rate})
        return pd.DataFrame(rows)

    def fx_history(self, iso3: str, start: str | None = None,
                   end: str | None = None) -> pd.DataFrame:
        """Monthly FX history for a single currency vs USD.

        Returns DataFrame with columns: date, value (USD per unit of local).
        """
        entry = FX_CURRENCY_MAP.get(iso3.upper())
        if entry is None:
            print(f'[YFinance] no FX mapping for {iso3}')
            return pd.DataFrame(columns=['date', 'value'])
        ticker, is_inverse = entry
        if ticker == '__USD__':
            return pd.DataFrame(columns=['date', 'value'])

        df = self._fetch_ticker(ticker, start, end)
        if df.empty:
            return df
        if is_inverse:
            df['value'] = round(1.0 / df['value'], 8)
        return df

    # ------------------------------------------------------------------
    # Generic accessor
    # ------------------------------------------------------------------

    def ticker(self, symbol: str, start: str | None = None,
               end: str | None = None) -> pd.DataFrame:
        """Fetch any Yahoo Finance ticker's monthly close history.

        Args:
            symbol: Yahoo Finance ticker (e.g. 'AAPL', 'EURUSD=X', '^GSPC').
            start/end: Date bounds in 'YYYY-MM-DD' format.

        Returns DataFrame with columns: date, value.
        """
        return self._fetch_ticker(symbol, start, end)
