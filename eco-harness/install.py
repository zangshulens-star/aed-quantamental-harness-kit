"""
Eco Data API Harness v2.0 — Self-Installer.

Usage:
    python install.py              # Install all dependencies
    python install.py --check      # Check what's installed / missing
    python install.py --upgrade    # Upgrade all packages to latest
"""
import subprocess
import sys
import os
import importlib


REQUIREMENTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')

# (pip_package, import_name, required_for)
DEPENDENCY_MAP = [
    ('pandas', 'pandas', 'All modules'),
    ('requests', 'requests', 'All modules'),
    ('python-dotenv', 'dotenv', 'API key loading'),
    ('fredapi', 'fredapi', 'eh.us.* — FRED data'),
    ('akshare', 'akshare', 'eh.cn.* — China macro'),
    ('wbgapi', 'wbgapi', 'eh.global_.* — World Bank WDI'),
    ('dbnomics', 'dbnomics', 'eh.global_.dbnomics + imf_dot'),
    ('opensdmx', 'opensdmx', 'eh.sdmx.* — OECD/ECB/Eurostat'),
    ('boj-api', 'boj_api', 'eh.jp.* — Bank of Japan'),
    ('numpy', 'numpy', 'ucdp.*'),
    ('beautifulsoup4', 'bs4', 'pbc_swap.*'),
    ('yfinance', 'yfinance', 'eh.yfinance.* — Gold, FX, stocks, MOVE'),
    ('tavily-python', 'tavily', 'eh.tavily.* — Web search'),
    ('playwright', 'playwright', 'eh.cbo.* — CBO data'),
    ('pyreadstat', 'pyreadstat', 'gsdb.* — GSDB .dta files (optional)'),
]

_OPTIONAL = {'pyreadstat', 'playwright', 'tavily-python'}


def check_installation():
    """Check which dependencies are installed and which are missing."""
    installed = []
    missing = []

    for pip_name, import_name, required_for in DEPENDENCY_MAP:
        try:
            importlib.import_module(import_name)
            installed.append((pip_name, required_for))
        except ImportError:
            missing.append((pip_name, required_for))

    return installed, missing


def install_dependencies(upgrade: bool = False):
    """pip install all requirements."""
    print('=' * 60)
    print('Eco Data API Harness v2.0 — Installing dependencies...')
    print('=' * 60)

    cmd = [sys.executable, '-m', 'pip', 'install']
    if upgrade:
        cmd.append('--upgrade')
    cmd.extend(['-r', REQUIREMENTS])

    try:
        subprocess.check_call(cmd)
        print('\n[OK] All packages installed.')
    except subprocess.CalledProcessError as e:
        print(f'\n[ERROR] pip install failed: {e}')
        print('Try running: pip install -r', REQUIREMENTS)
        sys.exit(1)


def post_install():
    """Run post-install steps."""
    # Playwright browser
    try:
        import playwright
        print('\nInstalling Playwright Chromium browser...')
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install', 'chromium'])
        print('[OK] Playwright Chromium installed.')
    except ImportError:
        pass
    except Exception as e:
        print(f'[WARN] Playwright browser install failed: {e}')
        print('  Run manually: playwright install chromium')


def print_api_key_guide():
    """Print API key setup instructions."""
    print('\n' + '=' * 60)
    print('API Key Setup Guide')
    print('=' * 60)
    print("""
The following APIs require registration (all free):

  FRED API Key
    Env var: FRED_API_KEY
    Enables: eh.us.* (FRED economic data)
    Register: https://fred.stlouisfed.org/docs/api/api_key.html

  EIA API Key
    Env var: EIA_API_KEY
    Enables: eh.energy.* (crude oil, natural gas prices)
    Register: https://www.eia.gov/opendata/

  UCDP API Token
    Env var: UCDP_API_TOKEN
    Enables: eh.ucdp.* (conflict event data)
    Register: https://ucdp.uu.se/downloads/

  UN Comtrade API Key
    Env var: UNCOMTRADE_API_KEY
    Enables: eh.comtrade.* (bilateral trade data)
    Register: https://comtradeplus.un.org/

  Tavily API Key
    Env var: TAVILY_API_KEY
    Enables: eh.tavily.* (web search)
    Register: https://tavily.com/

All keys go in a .env file or environment variables:
    echo 'FRED_API_KEY=your_key_here' >> .env

The following DO NOT require API keys:
  - Yahoo Finance (yfinance)
  - World Bank WDI / WGI
  - IMF WEO / IFS / DOT / COFER (via dbnomics & SDMX)
  - BIS statistics
  - OECD / ECB / Eurostat SDMX
  - Bank of Japan
  - OFAC sanctions
  - IPU parliamentary data
  - UN voting data (Harvard Dataverse)
  - SIPRI arms transfers
  - CBO budget data
  - OpenSanctions / GSDB (local CSV)
""")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Eco Data API Harness v2.0 — Self-Installer')
    parser.add_argument('--upgrade', action='store_true',
                        help='Upgrade all packages to latest versions')
    parser.add_argument('--check', action='store_true',
                        help='Check installation status only (no changes)')
    parser.add_argument('--no-post-install', action='store_true',
                        help='Skip post-install steps (Playwright browser)')

    args = parser.parse_args()

    if args.check:
        installed, missing = check_installation()
        print('=' * 60)
        print('Eco Data API Harness v2.0 — Installation Status')
        print('=' * 60)
        for pip_name, req in installed:
            print(f'  [OK]    {pip_name:30s} ({req})')
        for pip_name, req in missing:
            is_opt = pip_name in _OPTIONAL
            tag = '[MISS]' if not is_opt else '[OPT] '
            print(f'  {tag} {pip_name:30s} ({req})')
        print(f'\nInstalled: {len(installed)}/{len(DEPENDENCY_MAP)}')
        if missing:
            print(f'Missing: {len(missing)}')
            print('Run: python install.py')
        return

    install_dependencies(upgrade=args.upgrade)

    if not args.no_post_install:
        post_install()

    print('\n[OK] Eco Data API Harness v2.0 installation complete.')
    print_api_key_guide()


if __name__ == '__main__':
    main()