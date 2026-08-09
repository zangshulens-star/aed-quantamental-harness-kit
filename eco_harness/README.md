# Eco Data API Harness v2.0

Unified macroeconomic + geopolitical data access layer. 22 data sources, single import.

## Quick Install

```bash
cd bundle
python install.py
```

This installs all Python dependencies + Playwright Chromium. Use `--check` to see what's already installed.

## Quick Start

```python
from eco_harness import EcoHarness

eh = EcoHarness(fred_api_key='your_fred_key')

# US macro
df = eh.us.gdp()
df = eh.us.cpi()

# Markets
df = eh.yfinance.gold()
df = eh.yfinance.sp500()
df = eh.yfinance.move_index()

# China macro
df = eh.cn.m2()
df = eh.cn.pmi()

# Geopolitical
df = eh.ucdp.battle_deaths_annual()
```

## Data Sources (22)

| Category | Module | Access | API Key |
|----------|--------|--------|---------|
| **US Macro** | `eh.us.*` | FRED + Treasury | FRED |
| **China Macro** | `eh.cn.*` | AKShare | None |
| **Global** | `eh.global_.*` | World Bank WDI | None |
| **SDMX** | `eh.sdmx.*` | OECD / ECB / Eurostat | None |
| **Japan** | `eh.jp.*` | Bank of Japan | None |
| **Energy** | `eh.energy.*` | EIA | EIA |
| **Conflict** | `eh.ucdp.*` | UCDP GED | UCDP |
| **Markets** | `eh.yfinance.*` | Yahoo Finance | None |
| **Trade** | `eh.comtrade.*` | UN Comtrade | UN Comtrade |
| **Fiscal** | `eh.cbo.*` | CBO | None |
| **Web Search** | `eh.tavily.*` | Tavily | Tavily |
| **BIS** | `bis.*` (standalone) | BIS | None |
| **WGI** | `wgi.*` (standalone) | World Bank WGI | None |
| **OFAC** | `ofac.*` (standalone) | OFAC SDN | None |
| **UN Voting** | `un_voting.*` (standalone) | Harvard Dataverse | None |
| **IPU** | `ipu.*` (standalone) | IPU | None |
| **PBoC Swap** | `pbc_swap.*` (standalone) | PBoC | None |
| **SIPRI Arms** | `sipri.*` (standalone) | SIPRI | None |
| **IMF DOT** | `imf_dot.*` (standalone) | IMF (dbnomics) | None |
| **IMF COFER** | `cofer.*` (standalone) | IMF SDMX | None |
| **OpenSanctions** | `opensanctions.*` (standalone) | Local CSV | None |
| **GSDB v4** | `gsdb.*` (standalone) | Local CSV/DTA | None |

## API Keys

5 of 22 sources require registration (all free):

| Source | Env Variable | Register |
|--------|-------------|----------|
| FRED | `FRED_API_KEY` | https://fred.stlouisfed.org/docs/api/api_key.html |
| EIA | `EIA_API_KEY` | https://www.eia.gov/opendata/ |
| UCDP | `UCDP_API_TOKEN` | https://ucdp.uu.se/downloads/ |
| UN Comtrade | `UNCOMTRADE_API_KEY` | https://comtradeplus.un.org/ |
| Tavily | `TAVILY_API_KEY` | https://tavily.com/ |

Set in `.env` or environment variables. All modules gracefully degrade (empty DataFrame + warning) when keys are missing.

## Directory Structure

```
eco-data-v2/
  README.md
  skill.md              # Agentic markdown reference (Claude skill)
  bundle/
    eco_harness.py      # EcoHarness v2.0 class
    __init__.py
    install.py          # Self-installer
    requirements.txt
    us.py               # FRED + US Treasury
    cn.py               # AKShare China
    global_.py           # World Bank WDI
    sdmx.py             # OECD / ECB / Eurostat
    jp.py               # Bank of Japan
    energy.py           # EIA
    ucdp.py             # UCDP conflict
    yfinance.py         # Yahoo Finance (gold, FX, stocks, MOVE, VIX)
    comtrade.py         # UN Comtrade
    tavily_search.py    # Tavily web search
    cbo.py              # CBO budget data
    bis.py              # BIS statistics
    wgi.py              # World Governance Indicators
    ofac.py             # OFAC sanctions
    un_voting.py        # UN voting
    ipu.py              # IPU parliamentary data
    pbc_swap.py         # PBoC swap lines
    sipri.py            # SIPRI arms transfers
    imf_dot.py          # IMF Direction of Trade
    cofer.py            # IMF COFER FX reserves
    opensanctions.py    # OpenSanctions CSV
    gsdb.py             # GSDB v4 sanctions
```

## Return Format

All time-series methods return `pd.DataFrame` with `date` and `value` columns. Missing keys → empty DataFrame + warning, never crashes.