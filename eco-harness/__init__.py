"""
Eco Data API Harness v2.0 — Unified Macroeconomic + Geopolitical Data Access.

Usage:
    from bundle.eco_harness import EcoHarness
    eh = EcoHarness(fred_api_key='...')
    df = eh.us.gdp()
    df = eh.yfinance.gold()
"""
from .eco_harness import EcoHarness

__all__ = ["EcoHarness"]
