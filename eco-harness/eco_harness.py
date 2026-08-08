"""
Eco Data API Harness v2.0 — unified macroeconomic + geopolitical data access.

Standalone bundle edition. All imports are relative to the bundle package.

Class-based harnesses (via EcoHarness):
  us/         FRED + US Treasury
  cn/         AKShare (China macro)
  global_/    World Bank WDI + DBnomics
  sdmx/       OECD + ECB + Eurostat (via opensdmx)
  jp/         Bank of Japan
  energy/     EIA
  ucdp/       UCDP conflict data (GED API v26.1)
  yfinance/   Yahoo Finance — gold, FX, crude, stocks, MOVE  [v2.0]
  comtrade/   UN Comtrade trade ledger                       [v2.0]
  tavily/     Tavily web search                              [v2.0]
  cbo/        Congressional Budget Office data               [v2.0]

Module-level (standalone import):
  bis/        BIS credit statistics
  wgi/        World Governance Indicators
  ofac/       OFAC SDN sanctions
  un_voting/  UNGA ideal points
  ipu/        IPU parliamentary data
  pbc_swap/   PBoC swap lines
  sipri/      SIPRI arms transfers                          [v2.0]
  imf_dot/    IMF Direction of Trade via DBnomics           [v2.0]
  cofer/      IMF COFER FX reserves via SDMX                [v2.0]
  opensanctions/  OpenSanctions CSV loader                  [v2.0]
  gsdb/       GSDB v4 sanctions database loader             [v2.0]

Usage:
    from bundle.eco_harness import EcoHarness
    eh = EcoHarness(fred_api_key='...')
    df = eh.us.gdp()
    df = eh.yfinance.gold()
"""

from dotenv import load_dotenv
load_dotenv()

from .us import USHarness
from .cn import CNHarness
from .global_ import GlobalHarness
from .sdmx import SDMXHarness
from .jp import JPHarness
from .energy import EnergyHarness
from .ucdp import UCDPHarness
from .yfinance import YFinanceHarness
from .comtrade import ComtradeHarness
try:
    from .tavily_search import TavilyHarness
    _HAS_TAVILY = True
except ImportError:
    _HAS_TAVILY = False
from .cbo import CBOHarness


class EcoHarness:
    __slots__ = (
        'us', 'cn', 'global_', 'sdmx', 'jp', 'energy', 'ucdp',
        'yfinance', 'comtrade', 'tavily', 'cbo',
    )

    def __init__(self, fred_api_key: str = '', eia_api_key: str = '',
                 comtrade_api_key: str = '', tavily_api_key: str = ''):
        self.us = USHarness(fred_api_key)
        self.cn = CNHarness()
        self.global_ = GlobalHarness()
        self.sdmx = SDMXHarness()
        self.jp = JPHarness()
        self.energy = EnergyHarness(eia_api_key)
        self.ucdp = UCDPHarness()
        self.yfinance = YFinanceHarness()
        self.comtrade = ComtradeHarness(comtrade_api_key)
        self.tavily = TavilyHarness(tavily_api_key) if _HAS_TAVILY else None  # optional: pip install tavily-python
        self.cbo = CBOHarness()

    def __repr__(self):
        return 'EcoHarness v2.0 (us/cn/global_/sdmx/jp/energy/ucdp/yfinance/comtrade/tavily/cbo)'