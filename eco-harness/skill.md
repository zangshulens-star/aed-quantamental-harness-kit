---
name: eco-data-v2
description: Eco Data API Harness v2.0 — unified macroeconomic + geopolitical data access layer. Use when fetching FRED, World Bank, IMF, BIS, OECD, Yahoo Finance, UN Comtrade, CBO, OFAC, UCDP conflict, SIPRI arms, or any cross-source economic indicator. Covers 22+ data sources through a single import.
---

# Eco Data API Harness v2.0

Unified macroeconomic + geopolitical data access layer. Single import, 22+ data sources,
standardised DataFrame output.

## Quick Start

```python
from bundle.eco_harness import EcoHarness

eh = EcoHarness(fred_api_key='your_fred_key')

# US macro
df = eh.us.gdp()              # GDP (Billions, SAAR, Quarterly)
df = eh.us.cpi()              # CPI (Monthly)
df = eh.us.treasury_10y()     # 10Y Treasury yield (Daily)

# China macro
df = eh.cn.cpi()              # China CPI (Monthly)
df = eh.cn.pmi()              # Manufacturing PMI

# Global macro
df = eh.global_.gdp('CHN')    # China GDP (World Bank)
df = eh.global_.gdp_growth('USA')

# Market data (v2.0)
df = eh.yfinance.gold()       # Gold futures (USD/oz)
df = eh.yfinance.crude_oil()  # WTI crude (USD/barrel)
rate = eh.yfinance.fx_pair('JPY')  # USD/JPY spot rate

# Trade (v2.0)
df = eh.comtrade.bilateral_trade('USA', 'CHN', 2024)

# Web search (v2.0)
df = eh.tavily.search('US federal debt outlook 2026')

# CBO budget (v2.0)
df = eh.cbo.budget_outlook()
```

## Trigger

Invoke this skill when the user needs to:
- Fetch macroeconomic indicators (GDP, CPI, unemployment, trade, etc.)
- Pull market data (gold, FX, crude oil, stock indices, MOVE, VIX)
- Query geopolitical data (sanctions, conflict events, UN voting, arms transfers)
- Access fiscal data (CBO budget projections, IMF COFER reserves, debt statistics)
- Do any cross-source economic data gathering

## Bundle Structure

```
eco-data-v2/
  skill.md              # This file — master agentic markdown guide
  bundle/
    __init__.py         # Package exports (EcoHarness)
    eco_harness.py      # Main EcoHarness v2.0 class
    install.py          # Self-installer
    requirements.txt    # Python dependencies

    # === Class-based harnesses (accessed via eh.xxx) ===
    us.py               # FRED + US Treasury (20 methods)
    cn.py               # AKShare China macro (17 methods)
    global_.py          # World Bank WDI + DBnomics
    sdmx.py             # OECD + ECB + Eurostat SDMX
    jp.py               # Bank of Japan
    energy.py           # EIA crude oil / natural gas
    ucdp.py             # UCDP conflict data (GED v26.1)
    yfinance.py         # [v2.0] Yahoo Finance — gold, FX, stocks, MOVE, VIX
    comtrade.py         # [v2.0] UN Comtrade trade ledger
    tavily_search.py    # [v2.0] Tavily web search
    cbo.py              # [v2.0] CBO budget / economic projections

    # === Module-level (standalone import) ===
    bis.py              # BIS credit statistics
    wgi.py              # World Governance Indicators (6 dimensions)
    ofac.py             # OFAC SDN sanctions list
    un_voting.py        # UNGA ideal point estimates
    ipu.py              # IPU parliamentary data
    pbc_swap.py         # PBoC bilateral swap lines
    sipri.py            # [v2.0] SIPRI arms transfers
    imf_dot.py          # [v2.0] IMF Direction of Trade via DBnomics
    cofer.py            # [v2.0] IMF COFER FX reserves via SDMX
    opensanctions.py    # [v2.0] OpenSanctions CSV loader
    gsdb.py             # [v2.0] GSDB v4 sanctions database loader
```

---

## Module Reference — Class-Based (via EcoHarness)

All class-based harnesses are accessed as attributes of the `EcoHarness` instance.
Every time-series method returns a `pandas.DataFrame` with `date` and `value` columns, sorted by date.
All time-series methods accept optional `start` / `end` string parameters (`'YYYY-MM-DD'` format).

### eh.us — FRED + US Treasury

| Method | FRED Code | Description | Frequency |
|--------|-----------|-------------|-----------|
| `gdp(start, end)` | GDP | Nominal GDP (Billions, SAAR) | Q |
| `cpi(start, end)` | CPIAUCSL | CPI (1982-84=100) | M |
| `core_cpi(start, end)` | CPILFESL | Core CPI ex Food/Energy | M |
| `unemployment(start, end)` | UNRATE | Unemployment Rate (%) | M |
| `fed_funds(start, end)` | FEDFUNDS | Fed Funds Rate (%) | M |
| `treasury_10y(start, end)` | DGS10 | 10Y Treasury Yield (%) | D |
| `treasury_2y(start, end)` | DGS2 | 2Y Treasury Yield (%) | D |
| `treasury_3m(start, end)` | DTB3 | 3M Treasury Bill (%) | D |
| `nonfarm(start, end)` | PAYEMS | Nonfarm Payrolls (thousands) | M |
| `m2(start, end)` | M2SL | M2 Money Supply | M |
| `industrial(start, end)` | INDPRO | Industrial Production Index | M |
| `retail_sales(start, end)` | RSXFSN | Retail Sales | M |
| `trade_balance(start, end)` | BOPGSTB | Trade Balance | M |
| `debt_gdp(start, end)` | GFDEGDQ188S | Federal Debt % GDP | Q |
| `deficit_pct(start, end)` | FYFSGDA188S | Federal Deficit % GDP | A |
| `mortgage_30y(start, end)` | MORTGAGE30US | 30Y Fixed Mortgage Rate | W |
| `ism_mfg(start, end)` | INDPRO | ISM Manufacturing (industrial proxy) | M |
| `get(code, start, end)` | *any* | Arbitrary FRED series by code | — |
| `search(query, limit=10)` | — | Search FRED series metadata | — |

**Static methods (no API key):**
| Method | Description |
|--------|-------------|
| `treasury_debt_latest()` | Latest total public debt outstanding |
| `treasury_rates_of_exchange(country='China')` | USD/foreign currency exchange rate |
| `treasury_avg_interest_rates(start)` | Average interest rates by security type |

### eh.cn — China Macro (AKShare)

| Method | Description |
|--------|-------------|
| `gdp()` | GDP (quarterly cumulative, CNY 100M) |
| `gdp_yoy()` | GDP YoY growth rate |
| `cpi()` | CPI monthly |
| `ppi()` | PPI monthly |
| `pmi()` | Manufacturing PMI |
| `non_manufacturing_pmi()` | Non-manufacturing PMI |
| `m2()` | M2 money supply |
| `total_social_financing()` | Aggregate social financing |
| `lpr()` | Loan Prime Rate (1Y) |
| `foreign_reserves()` | FX reserves |
| `industrial_production()` | Industrial value-added YoY |
| `fixed_asset_investment()` | Fixed asset investment YoY |
| `retail_sales()` | Consumer goods retail sales YoY |
| `trade_balance()` | Trade balance (USD) |
| `new_house_price()` | New house price index (70 cities) |
| `electricity()` | Electricity consumption |
| `freight()` | Freight volume |

### eh.global_ — World Bank WDI + DBnomics

| Method | WB Code | Description |
|--------|---------|-------------|
| `gdp(country, mrv=5)` | NY.GDP.MKTP.CD | GDP (current USD) |
| `gdp_per_capita(country, mrv=5)` | NY.GDP.PCAP.CD | GDP per capita (current USD) |
| `gdp_growth(country, mrv=5)` | NY.GDP.MKTP.KD.ZG | GDP growth (annual %) |
| `cpi(country, mrv=5)` | FP.CPI.TOTL.ZG | CPI inflation (annual %) |
| `population(country, mrv=5)` | SP.POP.TOTL | Total population |
| `trade_balance(country, mrv=5)` | NE.RSB.GNFS.ZS | Trade balance % GDP |
| `get(indicator, country, mrv=5)` | *any | Arbitrary WDI indicator |
| `search(query)` | — | Search WDI indicators |
| `dbnomics(provider, dataset, series)` | — | Static: any DBnomics series |

### eh.sdmx — OECD + ECB + Eurostat

| Method | Description |
|--------|-------------|
| `oecd(dataset='QNA', country='USA', freq='Q')` | OECD datasets (QNA, CPI, KEI, BOP) |
| `ecb(dataset='EXR', freq='D', currency='USD')` | ECB exchange rates / yield curves |
| `eurostat(dataset='prc_hicp_manr', country='DE')` | Eurostat HICP inflation |
| `search(keyword, provider='oecd')` | Search datasets |
| `list_datasets(provider='oecd')` | List provider datasets |

### eh.jp — Bank of Japan

| Method | Description |
|--------|-------------|
| `fx(pair='USDJPY', start, end)` | FX rates |
| `tankan(start, end)` | Tankan survey (large mfg) |
| `get(db, codes, start, end)` | Arbitrary BOJ series |

### eh.energy — EIA

| Method | Description |
|--------|-------------|
| `crude_price()` | WTI crude oil spot price (weekly) |
| `natural_gas_price()` | Henry Hub natural gas spot price (monthly) |

### eh.ucdp — UCDP Conflict Data

| Method | Description |
|--------|-------------|
| `is_available` (property) | API connectivity check |
| `battle_deaths_annual(iso3_list, start, end)` | Annual panel: deaths + events |
| `conflict_absence_index(iso3_list)` | Score 0-100 (100 = no conflict) |
| `fetch_ged_events(iso3, start, end)` | Raw GED event records |

### eh.yfinance — Yahoo Finance [v2.0]

**No API key required.**

| Method | Ticker | Description |
|--------|--------|-------------|
| `gold(start, end)` | GC=F | Gold futures (USD/oz) |
| `crude_oil(start, end)` | CL=F | WTI crude (USD/barrel) |
| `brent_crude(start, end)` | BZ=F | Brent crude (USD/barrel) |
| `natural_gas(start, end)` | NG=F | Henry Hub natural gas |
| `bitcoin(start, end)` | BTC-USD | Bitcoin (USD) |
| `vix(start, end)` | ^VIX | CBOE Volatility Index |
| `move_index(start, end)` | ^MOVE | ICE BofA MOVE (bond vol) |
| `sp500(start, end)` | ^GSPC | S&P 500 |
| `nasdaq(start, end)` | ^IXIC | NASDAQ Composite |
| `stock_index(iso3, board='main')` | — | Country stock index (25 countries) |
| `stock_indices_all(iso3)` | — | All boards for a country |
| `fx_pair(iso3)` | — | Latest FX spot (USD per local unit) |
| `fx_basket(iso3_list)` | — | Latest FX spot for multiple currencies |
| `fx_history(iso3, start, end)` | — | Monthly FX history |
| `ticker(symbol, start, end)` | *any | Arbitrary ticker |
| `list_countries()` | — | List countries with stock mappings |

### eh.comtrade — UN Comtrade [v2.0]

**Requires:** `UNCOMTRADE_API_KEY` env var. Free registration at comtradeplus.un.org.

| Method | Description |
|--------|-------------|
| `trade_flow(reporter, partner, commodity, year, flow)` | Basic trade flow lookup |
| `bilateral_trade(reporter, partner, year)` | Exports + imports + balance |
| `total_trade(reporter, year)` | Total exports + imports |
| `top_partners(reporter, year, n=10, flow='X')` | Top N trading partners |
| `trade_balance_trend(reporter, start_year, end_year)` | Multi-year balance trend |

### eh.tavily — Tavily Web Search [v2.0]

**Requires:** `TAVILY_API_KEY` env var. Free registration at tavily.com (1,000 searches/month).

| Method | Description |
|--------|-------------|
| `search(query, max_results=10)` | General web search → DataFrame |
| `search_news(query, days=7, max_results=10)` | News search with recency |
| `economic_data_search(topic, max_results=10)` | Economic-context search |
| `sanctions_search(entity_name, max_results=10)` | Sanctions/regulatory search |

### eh.cbo — Congressional Budget Office [v2.0]

**No API key.** Requires Playwright Chromium for fallback scraping.

| Method | Description |
|--------|-------------|
| `budget_outlook()` | 10-year budget projections |
| `long_term_outlook()` | 30-year long-term outlook |
| `historical_budget()` | Historical budget data (1962+) |
| `debt_to_gdp()` | Federal debt % GDP extraction |
| `list_series()` | Available CBO series |

---

## Module Reference — Module-Level (Standalone Import)

These are imported directly from the bundle, not accessed via EcoHarness:

```python
from bundle.bis import credit_private, total_credit
from bundle.wgi import get_all_wgi, get_indicator
from bundle.ofac import fetch_sdn, get_sanctions_by_country
from bundle.un_voting import get_ideal_point, get_voting_distance
from bundle.ipu import get_chambers, get_sovereign_chambers
from bundle.pbc_swap import get_swap_lines
from bundle.sipri import fetch_arms_transfers, us_exports, china_exports
from bundle.imf_dot import bilateral_trade, total_exports, total_imports
from bundle.cofer import usd_share, currency_shares, cny_share_trend
from bundle.opensanctions import load_entities, search_by_country, sanctions_summary
from bundle.gsdb import load, sanctions_by_target, active_sanctions
```

### bis — BIS Credit Statistics

| Function | Description |
|----------|-------------|
| `credit_private(countries, freq='Q')` | Private non-financial sector credit (% GDP) |
| `total_credit(countries, freq='Q')` | Total credit all sectors (% GDP) |
| `property_prices(countries, freq='Q')` | Residential property prices |
| `fetch(dataflow, ref_area, freq, start, end)` | Arbitrary BIS dataflow |
| `list_countries(dataflow)` | Available countries in dataflow |

### wgi — World Governance Indicators

| Function | Description |
|----------|-------------|
| `get_indicator(indicator, country, date_range)` | Single WGI indicator (CC/GE/PV/RQ/RL/VA) |
| `get_all_wgi(country)` | All 6 WGI indicators for a country |

6 dimensions: CC (Control of Corruption), GE (Government Effectiveness),
PV (Political Stability), RQ (Regulatory Quality), RL (Rule of Law), VA (Voice & Accountability).

### ofac — OFAC Sanctions

| Function | Description |
|----------|-------------|
| `fetch_sdn(max_entries)` | Download + parse full SDN XML |
| `get_sanctions_by_program()` | Entity counts per sanction program |
| `get_sanctions_by_country()` | Entity counts per country |
| `get_program_sanctions(program)` | Entities in a specific program |
| `get_relevant_sanctions()` | Entities in 40 key programs |
| `count_sanctioned_countries()` | {iso3: entity_count} for 25 sovereign countries |

### un_voting — UNGA Ideal Points

| Function | Description |
|----------|-------------|
| `fetch_ideal_points()` | Full dataset (1946-2025) |
| `get_ideal_point(iso3, min_year=2020)` | Single country time series |
| `get_ideal_points_multi(iso3_list, min_year=2020)` | Multi-country ideal points |
| `get_unga_alignment_2025()` | Latest year snapshot (sorted) |
| `get_voting_distance(iso3_a, iso3_b='USA')` | Ideal point distance between two countries |
| `get_sovereign_ideal_points(min_year=2020)` | 25 sovereign countries |

### ipu — IPU Parliamentary Data

| Function | Description |
|----------|-------------|
| `list_countries()` | All countries in IPU database |
| `get_chambers(iso2)` | Parliament info (seats, elections, electoral system) |
| `get_seats_by_party(iso2)` | Seat distribution by party |
| `get_sovereign_chambers()` | 25 sovereign countries |

### pbc_swap — PBoC Swap Lines

| Function | Description |
|----------|-------------|
| `scrape_recent()` | Scrape recent agreements from PBoC |
| `get_swap_lines(include_expired=False)` | All known swap lines (28 agreements) |

### sipri — SIPRI Arms Transfers [v2.0]

| Function | Description |
|----------|-------------|
| `fetch_arms_transfers()` | Full dataset (live scrape → manual CSV → static fallback) |
| `by_supplier(supplier)` | Filter by supplier country |
| `by_recipient(iso3)` | Filter by recipient country |
| `us_exports()` | US arms exports — top recipients |
| `china_exports()` | China arms exports — top recipients |
| `top_suppliers(n=5)` | Top N arms suppliers by TIV |
| `top_recipients(n=10)` | Top N arms recipients by TIV |

### imf_dot — IMF Direction of Trade [v2.0]

| Function | Description |
|----------|-------------|
| `bilateral_trade(reporter_iso2, partner_iso2, year)` | Exports from reporter to partner |
| `total_exports(iso2, year)` | Total goods exports |
| `total_imports(iso2, year)` | Total goods imports |
| `trade_balance_trend(iso2, start_year, end_year)` | Exports - imports time series |

### cofer — IMF COFER FX Reserves [v2.0]

| Function | Description |
|----------|-------------|
| `usd_share()` | USD share of allocated reserves (%) |
| `currency_shares()` | All 8 currencies + Other (% of allocated) |
| `cny_share_trend()` | CNY/RMB share (de-dollarisation indicator) |
| `total_allocated_reserves()` | Total allocated reserves (USD) |

### opensanctions — OpenSanctions CSV Loader [v2.0]

| Function | Description |
|----------|-------------|
| `load_summary(path)` | Per-country sanctions summary |
| `load_entities(path)` | Per-entity sanctions records |
| `search_by_country(iso3)` | All entities for a country |
| `search_by_name(query)` | Case-insensitive entity search |
| `search_by_sender(sender)` | Filter by sanctioning authority (US/UN/EU/UK) |
| `sanctions_summary(iso3)` | Country summary |
| `entity_count()` | Total entities |

### gsdb — GSDB v4 Sanctions Database [v2.0]

| Function | Description |
|----------|-------------|
| `load(path, force_reload)` | Load GSDB CSV/DTA |
| `sanctions_by_target(country)` | Sanctions targeting a country |
| `sanctions_by_sender(country)` | Sanctions imposed by a country |
| `sanctions_by_type(type)` | Filter by type (trade/arms/military/financial/travel) |
| `active_sanctions(year)` | Sanctions active in a given year |
| `sanctions_summary(target, sender)` | Pivot summary |
| `sanctions_count_trend(country)` | Active sanctions per year time series |

---

## Mandatory Rules

### R1: All API keys from environment variables
Never hardcode keys. Each harness reads from `os.environ.get('VAR_NAME', '')`.
Create a `.env` file in your project root:
```
FRED_API_KEY=your_key
EIA_API_KEY=your_key
UNCOMTRADE_API_KEY=your_key
TAVILY_API_KEY=your_key
UCDP_API_TOKEN=your_token
```

### R2: Lazy imports for heavy libraries
`yfinance`, `playwright`, `tavily`, `fredapi`, `dbnomics`, `wbgapi` are imported
only on first use. Importing `EcoHarness` alone does not load any heavy library.

### R3: Standard DataFrame return format
All time-series methods return `pandas.DataFrame` with columns `date` and `value`,
sorted by date ascending. The `date` column is string format `YYYY-MM-DD`.

### R4: Graceful degradation
When an API key is missing, methods return an empty DataFrame (columns preserved)
and print a one-line warning. They never crash. This allows partial EcoHarness
usage with only the keys you have.

### R5: Rate limit awareness
- FRED: 120 req/min (free tier)
- UN Comtrade: ~500 req/day (free tier, 0.6s built-in delay)
- Tavily: 1,000 searches/month (free tier)
- AKShare: upstream sites may throttle — batch with ≥1s interval
- World Bank / DBnomics / OECD SDMX / BIS / BoJ: no hard limits

### R6: Caching
`opensdmx` (SDMX) and `dbnomics` have built-in SQLite+Parquet caches.
CBO stores downloaded Excel files locally (7-day cache).
All other modules re-fetch on each call — cache at the application layer.

---

## Unified API Key Setup

All API keys go in a `.env` file or system environment variables.
Create a `.env` file in your project root:

| Data Source | Env Variable | Enables | Registration URL |
|-------------|-------------|---------|-----------------|
| **FRED** (St. Louis Fed) | `FRED_API_KEY` | eh.us.* (US macro) | https://fred.stlouisfed.org/docs/api/api_key.html |
| **EIA** (US Energy) | `EIA_API_KEY` | eh.energy.* (oil & gas) | https://www.eia.gov/opendata/ |
| **UCDP** (Uppsala Conflict) | `UCDP_API_TOKEN` | eh.ucdp.* (conflict data) | https://ucdp.uu.se/downloads/ |
| **UN Comtrade** | `UNCOMTRADE_API_KEY` | eh.comtrade.* (trade data) | https://comtradeplus.un.org/ |
| **Tavily** (Web Search) | `TAVILY_API_KEY` | eh.tavily.* (search) | https://tavily.com/ |

### No API Key Required

The following 17 data sources are completely free and require no registration:
Yahoo Finance, World Bank WDI, World Bank WGI, IMF WEO/IFS/GFSMAB/DOT, BIS,
OECD SDMX, ECB, Eurostat, Bank of Japan, OFAC, IPU, UN Voting (Harvard Dataverse),
SIPRI, CBO, OpenSanctions, GSDB, PBoC.

---

## Installation

### Quick Install

```bash
# 1. Extract the eco-data-v2/ directory into .claude/skills/
# 2. Install dependencies
cd .claude/skills/eco-data-v2/bundle
python install.py

# 3. Install Playwright browser (required for CBO)
python -m playwright install chromium

# 4. Check status
python install.py --check
```

### Manual Install

```bash
pip install -r bundle/requirements.txt
playwright install chromium
```

### Configure API Keys

```bash
# Create .env in your project root
cat >> ../../.env << 'EOF'
FRED_API_KEY=your_fred_key_here
UNCOMTRADE_API_KEY=your_comtrade_key_here
TAVILY_API_KEY=your_tavily_key_here
EOF
```

---

## Usage Patterns

### Pattern 1: Quick single-indicator fetch

```python
from bundle.eco_harness import EcoHarness
eh = EcoHarness(fred_api_key='...')

df = eh.us.gdp()
print(df.tail())
```

### Pattern 2: Cross-source comparison

```python
from bundle.eco_harness import EcoHarness
eh = EcoHarness()

# US vs China GDP growth
us_growth = eh.global_.gdp_growth('USA', mrv=20)
cn_growth = eh.global_.gdp_growth('CHN', mrv=20)

# US vs China 10Y yields
us_10y = eh.us.treasury_10y()
cn_10y = eh.cn.lpr()  # China doesn't have a deep 10Y market — LPR as proxy
```

### Pattern 3: Sovereign risk dashboard data pull

```python
from bundle.eco_harness import EcoHarness
from bundle import wgi, ofac, ucdp, cofer, sipri

eh = EcoHarness()

# Economic baseline
gdp = eh.global_.gdp('TUR')
cpi = eh.global_.cpi('TUR')
fx = eh.yfinance.fx_pair('TUR')

# Governance
gov = wgi.get_all_wgi('Turkey')

# Conflict exposure
conflict = ucdp.UCDPHarness().conflict_absence_index()

# Sanctions
sanctions = ofac.count_sanctioned_countries()

# Arms imports
arms = sipri.by_recipient('TUR')
```

### Pattern 4: Daily market monitoring

```python
from bundle.eco_harness import EcoHarness

eh = EcoHarness()

# Daily market snapshot
gold = eh.yfinance.gold()
oil = eh.yfinance.crude_oil()
spx = eh.yfinance.sp500()
vix = eh.yfinance.vix()
move = eh.yfinance.move_index()
usd_jpy = eh.yfinance.fx_pair('JPN')

# 10Y yield
yield_10y = eh.us.treasury_10y()
```

### Pattern 5: Use module-level functions directly (no EcoHarness instance needed)

```python
from bundle import bis, cofer, imf_dot, sipri

# BIS credit data
credit = bis.credit_private(['US', 'CN', 'JP'])

# IMF COFER de-dollarisation
cny_share = cofer.cny_share_trend()

# IMF trade direction
trade = imf_dot.bilateral_trade('US', 'CN', 2024)

# SIPRI arms
us_arms = sipri.us_exports()
```
