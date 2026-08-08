"""qh-coverage — Audit coverage analysis.

Scans paper Markdown/LaTeX files for quantitative claims and cross-references
against a claims.yaml registry to identify unregistered claims.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def _parse_args():
    p = argparse.ArgumentParser(
        prog="qh-coverage",
        description="Analyze paper coverage: find quantitative claims not yet in claims.yaml.",
    )
    p.add_argument("--paper", required=True, help="Path to paper directory (Markdown/LaTeX files)")
    p.add_argument("--claims", required=True, help="Path to claims.yaml registry")
    p.add_argument("--format", choices=["markdown", "latex"], default="markdown",
                   help="Paper format (default: markdown)")
    p.add_argument("--output", choices=["json", "markdown", "terminal"], default="terminal")
    return p.parse_args()


# ── Numerical claim extraction patterns ──────────────────────────

# Match: number + optional %/bps/x/pp suffix + optional context keywords
_NUM_PATTERN = re.compile(
    r'(\d+\.?\d*)\s*(%|bps|bp|x|pp|times|d|m|days|months|years)?',
)

# Keywords that signal a quantitative claim worth tracking
_QUANT_KEYWORDS = [
    r'sharpe\s*ratio', r'max\s*drawdown', r'maxdd', r'calmar',
    r'annuali[sz]ed\s*return', r'cagr', r'volatility', r'sharpe',
    r'hit\s*rate', r'win\s*rate', r'turnover', r'floor\s*hit',
    r'correlation', r'r\s*[\^]?2', r'p[i\s]*value', r't[- ]?stat',
    r'standard\s*deviation', r'mean|average|median',
    r'skew|kurtosis', r'percentile|quantile',
    r'回撤', r'夏普', r'波动', r'收益',  # Chinese keywords
]

_QUANT_RE = re.compile('|'.join(_QUANT_KEYWORDS), re.IGNORECASE)


def _extract_numeric_claims(text: str, source_file: str) -> List[Dict]:
    """Extract suspected quantitative claims from text using regex heuristics."""
    claims = []

    # Split text into sentences (roughly)
    sentences = re.split(r'(?<=[.!?\n])\s+', text)

    for sentence in sentences:
        # Must contain at least one number
        nums = _NUM_PATTERN.findall(sentence)
        if not nums:
            continue

        # Check for quantitative context keywords
        has_context = bool(_QUANT_RE.search(sentence))

        confidence = "high" if has_context else "low"

        # Extract the numeric values
        values = []
        for val, unit in nums:
            values.append(f"{val}{unit}" if unit else val)

        claims.append({
            "sentence": sentence.strip()[:200],
            "values": values,
            "confidence": confidence,
            "source_file": source_file,
        })

    return claims


def _load_claim_ids(claims_path: str) -> Set[str]:
    """Load known claim IDs from claims.yaml for cross-referencing."""
    try:
        from ..core.loader import load_claims
        registry = load_claims(claims_path)
        # Store claim text signatures for fuzzy matching
        return {c.id: c.text.lower() for c in registry.claims}
    except Exception:
        return {}


def _fuzzy_match(extracted_sentence: str, known_texts: Dict[str, str]) -> bool:
    """Check if extracted claim roughly matches any known claim text.

    Simple heuristic: check if any numeric value + keyword pair matches.
    """
    sentence_lower = extracted_sentence.lower()
    for claim_text in known_texts.values():
        # Very rough: check word overlap
        s_words = set(sentence_lower.split())
        c_words = set(claim_text.split())
        if len(s_words & c_words) >= 3:
            return True
    return False


def analyze_coverage(paper_dir: str, claims_path: str, fmt: str = "markdown") -> Dict:
    """Analyze paper coverage against claims registry."""
    paper_path = Path(paper_dir)
    if not paper_path.exists():
        raise FileNotFoundError(f"Paper directory not found: {paper_dir}")

    # Collect all paper files
    ext = ".md" if fmt == "markdown" else ".tex"
    paper_files = list(paper_path.rglob(f"*{ext}"))
    if not paper_files:
        # Try both extensions
        paper_files = list(paper_path.rglob("*.md")) + list(paper_path.rglob("*.tex"))

    # Extract claims from paper
    all_extracted = []
    for pf in paper_files:
        try:
            text = pf.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        extracted = _extract_numeric_claims(text, str(pf.relative_to(paper_path)))
        all_extracted.extend(extracted)

    # Load known claims
    known_texts = _load_claim_ids(claims_path)

    # Cross-reference: which extracted claims are already registered?
    registered = []
    unregistered_high = []
    unregistered_low = []

    for claim in all_extracted:
        if _fuzzy_match(claim["sentence"], known_texts):
            registered.append(claim)
        elif claim["confidence"] == "high":
            unregistered_high.append(claim)
        else:
            unregistered_low.append(claim)

    total = len(all_extracted)
    covered = len(registered)

    # Group by chapter (source file)
    by_file: Dict[str, Dict] = {}
    for claim in all_extracted:
        f = claim["source_file"]
        if f not in by_file:
            by_file[f] = {"total": 0, "registered": 0, "unregistered_high": 0}
        by_file[f]["total"] += 1
        if claim in registered:
            by_file[f]["registered"] += 1
        elif claim in unregistered_high:
            by_file[f]["unregistered_high"] += 1

    return {
        "paper_dir": paper_dir,
        "claims_file": claims_path,
        "total_extracted": total,
        "registered": len(registered),
        "unregistered_high_confidence": len(unregistered_high),
        "unregistered_low_confidence": len(unregistered_low),
        "coverage_pct": round(covered / total * 100, 1) if total > 0 else 0.0,
        "by_file": by_file,
        "unregistered_high": unregistered_high[:20],  # Cap for output size
        "unregistered_low": unregistered_low[:10],
    }


def render_terminal(results: Dict) -> str:
    lines = []
    lines.append("=" * 64)
    lines.append(f"  Coverage Analysis")
    lines.append(f"  Paper:  {results['paper_dir']}")
    lines.append(f"  Claims: {results['claims_file']}")
    lines.append("=" * 64)
    lines.append(f"  Total extracted:      {results['total_extracted']}")
    lines.append(f"  Registered:           {results['registered']}")
    lines.append(f"  Unregistered (HIGH):  {results['unregistered_high_confidence']}")
    lines.append(f"  Unregistered (LOW):   {results['unregistered_low_confidence']}")
    lines.append(f"  Coverage:             {results['coverage_pct']}%")
    lines.append("")

    # By file
    lines.append("  By file:")
    for fname, stats in sorted(results["by_file"].items()):
        cov = round(stats["registered"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        lines.append(f"    {fname}: {stats['registered']}/{stats['total']} ({cov}%) [{stats['unregistered_high']} high-conf unregistered]")

    # Unregistered high-confidence examples
    if results["unregistered_high"]:
        lines.append(f"\n  Top unregistered (HIGH confidence):")
        for claim in results["unregistered_high"][:10]:
            lines.append(f"    [{claim['source_file']}] {claim['sentence'][:120]}...")
            lines.append(f"      Values: {', '.join(claim['values'])}")

    # Coverage gate
    cov = results["coverage_pct"]
    if cov < 60:
        lines.append(f"\n  GATE FAIL: Overall coverage {cov}% < 60%")
    elif cov < 80:
        lines.append(f"\n  GATE WARNING: Overall coverage {cov}% < 80%")
    else:
        lines.append(f"\n  GATE PASS: Overall coverage {cov}% >= 80%")

    return "\n".join(lines)


def render_json(results: Dict) -> str:
    import json
    # Remove full sentence lists for compact JSON
    out = {k: v for k, v in results.items() if k not in ("unregistered_high", "unregistered_low")}
    out["unregistered_high_count"] = results["unregistered_high_confidence"]
    out["unregistered_low_count"] = results["unregistered_low_confidence"]
    return json.dumps(out, indent=2, ensure_ascii=False, default=str)


def render_markdown(results: Dict) -> str:
    lines = []
    lines.append(f"# Coverage Analysis Report")
    lines.append(f"")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|------:|")
    lines.append(f"| Total extracted | {results['total_extracted']} |")
    lines.append(f"| Registered | {results['registered']} |")
    lines.append(f"| Unregistered (HIGH) | {results['unregistered_high_confidence']} |")
    lines.append(f"| Coverage | {results['coverage_pct']}% |")
    lines.append(f"")

    # By file table
    lines.append(f"| File | Total | Registered | Coverage | High-conf Unreg |")
    lines.append(f"|------|------:|-----------:|---------:|----------------:|")
    for fname, stats in sorted(results["by_file"].items()):
        cov = round(stats["registered"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        lines.append(f"| {fname} | {stats['total']} | {stats['registered']} | {cov}% | {stats['unregistered_high']} |")

    return "\n".join(lines)


def main():
    args = _parse_args()

    try:
        results = analyze_coverage(args.paper, args.claims, args.format)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(4)

    renders = {"terminal": render_terminal, "json": render_json, "markdown": render_markdown}
    renderer = renders.get(args.output, render_terminal)
    print(renderer(results))

    # Exit codes: 1 = overall < 60% coverage or any chapter < 60%
    cov = results["coverage_pct"]
    if cov < 60:
        sys.exit(1)

    for fname, stats in results["by_file"].items():
        file_cov = round(stats["registered"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        if file_cov < 60:
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
