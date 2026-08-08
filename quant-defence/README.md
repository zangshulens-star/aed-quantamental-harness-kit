# Quant Harness

Zero-config, pip-installable quantitative research defence toolbelt.

**Install < 60s. Onboard < 5min. Zero project dependencies beyond pandas/pyyaml/numpy.**

## Quick Start

```bash
# Install
pip install -e /path/to/quant_harness

# Initialize a project
python -m quant_harness.bootstrap --project-dir /path/to/your/project

# Verify claims
qh-verify --claims validation/claims.yaml --all

# Audit NaN degradation
qh-null-audit --panel data/panel.csv

# Check paper coverage
qh-coverage --paper paper/ --claims validation/claims.yaml
```

## CLI Tools

| Tool | Description | Status |
|------|-------------|--------|
| `qh-verify` | Claim verification against data/engine | MVP |
| `qh-null-audit` | NaN silent degradation detection | MVP |
| `qh-coverage` | Paper coverage analysis | MVP |
| `qh-version-check` | Version consistency checker | Phase 2 |
| `qh-auto-claims` | Auto-generate claims template | Phase 2 |
| `qh-regression` | Regression test runner | Phase 2 |
| `qh-sensitivity` | Parameter sensitivity scanner | Phase 3 |
| `qh-lookahead` | Look-ahead bias detection | Phase 3 |

## Claim Types

| Type | What it verifies |
|------|-----------------|
| `value_exact` | Latest value matches expected (with tolerance) |
| `value_range` | Value falls within [min, max] |
| `aggregate` | Sum/mean/max/min/count matches expected |
| `time_mask` | Condition holds during a time period |
| `cross_count` | Row count for cross-section condition |
| `set_equality` | Unique value sets match |

## License

MIT