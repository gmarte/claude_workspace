"""
allocate_contribution.py
Given the current portfolio and a contribution amount, calculates the optimal
allocation across ETFs to bring the portfolio closest to target weights.
Uses a pure gap-closing approach: never sells, never violates IPS bands.

Usage:
    python allocate_contribution.py --amount 3100
    python allocate_contribution.py --amount 3100 --positions path/to/positions.csv
    python allocate_contribution.py --amount 3100 --json
"""

import csv
import sys
import json
import argparse
from pathlib import Path
from datetime import date

try:
    import yaml
    def load_yaml(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
except ImportError:
    def load_yaml(path):
        raise SystemExit("PyYAML is required: pip install pyyaml")

SKILL_DIR = Path(__file__).resolve().parent.parent
POSITIONS_FILE = SKILL_DIR / "positions.csv"
TARGET_FILE = SKILL_DIR / "target_allocation.yaml"
CONFIG_FILE = SKILL_DIR / "portfolio_config.yaml"

MIN_PURCHASE = 50.0   # Don't create an order for less than $50


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_positions(path: Path) -> list[dict]:
    if not path.exists():
        print(f"ERROR: positions file not found: {path}", file=sys.stderr)
        sys.exit(1)
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            shares = float(row["shares"])
            price = float(row["last_price"])
            rows.append({
                "ticker":     row["ticker"].strip().upper(),
                "shares":     shares,
                "last_price": price,
                "value":      shares * price,
            })
    return rows


def load_targets(path: Path) -> dict:
    data = load_yaml(path)
    return data.get("holdings", {})


def load_config(path: Path) -> dict:
    return load_yaml(path)


# ── Core allocation logic ─────────────────────────────────────────────────────

def compute_allocation(positions: list[dict], targets: dict, contribution: float, config: dict) -> dict:
    """
    Gap-closing algorithm:
    1. Compute the "ideal" value of each position in the post-contribution portfolio.
    2. Calculate the gap = ideal - current for each position.
    3. Allocate contribution to positions with a positive gap, weighted by gap size.
    4. Skip positions with a negative gap (overweight — don't add more).
    5. Enforce minimum purchase size; redistribute any remainder.
    6. Adjust for rounding so the total equals contribution exactly.
    """
    constraints = config.get("constraints", {})
    min_purchase = constraints.get("minimum_purchase_usd", MIN_PURCHASE)

    current_values = {p["ticker"]: p["value"] for p in positions}
    current_prices = {p["ticker"]: p["last_price"] for p in positions}

    # Include positions in targets that don't exist yet
    all_tickers = set(current_values.keys()) | set(targets.keys())
    portfolio_value = sum(current_values.values())
    new_total = portfolio_value + contribution

    gaps: dict[str, float] = {}
    for ticker in all_tickers:
        if ticker == "CASH":
            continue
        target_pct = targets.get(ticker, {}).get("target_pct", 0.0)
        ideal_value = new_total * (target_pct / 100.0)
        current_value = current_values.get(ticker, 0.0)
        gap = ideal_value - current_value
        if gap > 0:
            gaps[ticker] = gap

    if not gaps:
        return {
            "error": "All positions are at or above target. No allocation needed.",
            "contribution": contribution,
            "allocations": {},
        }

    fractional_ok = config.get("platform", {}).get("fractional_shares", True)

    if not fractional_ok:
        # Whole-share mode — TradeStation rejects fractional/decimal quantities.
        # Greedily buy 1 share at a time of the ticker whose remaining gap covers
        # the largest fraction of its price; stop below 60% coverage so a single
        # share can never overshoot its target by more than ~40% of its price.
        # The unspent remainder stays in cash (total deployed <= contribution).
        remaining = contribution
        residual_gap = dict(gaps)
        share_counts = {t: 0 for t in gaps}
        while True:
            candidates = [
                t for t in gaps
                if 0 < current_prices.get(t, 0.0) <= remaining
                and residual_gap[t] / current_prices[t] >= 0.6
            ]
            if not candidates:
                break
            pick = max(candidates, key=lambda t: residual_gap[t] / current_prices[t])
            share_counts[pick] += 1
            residual_gap[pick] -= current_prices[pick]
            remaining -= current_prices[pick]
        rounded = {
            t: round(n * current_prices[t], 2)
            for t, n in share_counts.items()
            if n > 0 and n * current_prices[t] >= min_purchase
        }
    else:
        # Weight allocations proportional to gap, capped at actual gap
        total_gap = sum(gaps.values())
        raw_allocations = {
            ticker: min(gap, contribution * (gap / total_gap))
            for ticker, gap in gaps.items()
        }

        # Remove positions below minimum purchase threshold
        filtered = {t: v for t, v in raw_allocations.items() if v >= min_purchase}
        if not filtered:
            # Everything is tiny — just put it in the most underweight position
            most_underweight = max(gaps, key=gaps.get)
            filtered = {most_underweight: contribution}

        # Renormalize to sum to contribution
        total_raw = sum(filtered.values())
        normalized = {t: (v / total_raw) * contribution for t, v in filtered.items()}

        # Round to cents; fix rounding residual on largest allocation
        rounded = {t: round(v, 2) for t, v in normalized.items()}
        residual = round(contribution - sum(rounded.values()), 2)
        if residual != 0 and rounded:
            largest = max(rounded, key=rounded.get)
            rounded[largest] = round(rounded[largest] + residual, 2)

    # Build output rows with share estimates
    allocations = []
    for ticker, amount in sorted(rounded.items(), key=lambda x: -x[1]):
        price = current_prices.get(ticker, 0.0)
        shares_approx = amount / price if price > 0 else 0.0
        target_pct = targets.get(ticker, {}).get("target_pct", 0.0)
        current_val = current_values.get(ticker, 0.0)
        current_pct = (current_val / portfolio_value * 100) if portfolio_value > 0 else 0.0
        drift = current_pct - target_pct
        tax_note = targets.get(ticker, {}).get("tax_notes", "")[:80]

        allocations.append({
            "ticker":         ticker,
            "amount_usd":     amount,
            "current_price":  price,
            "shares_approx":  round(shares_approx, 4),
            "current_pct":    round(current_pct, 2),
            "target_pct":     target_pct,
            "drift":          round(drift, 2),
            "gap_usd":        round(gaps.get(ticker, 0.0), 2),
            "tax_note":       tax_note,
        })

    return {
        "report_date":     str(date.today()),
        "portfolio_value": portfolio_value,
        "contribution":    contribution,
        "new_total":       new_total,
        "total_allocated": sum(rounded.values()),
        "leftover_cash":   round(contribution - sum(rounded.values()), 2),
        "allocations":     allocations,
    }


# ── Tax efficiency advisory ───────────────────────────────────────────────────

def tax_advisory(allocations: list[dict], targets: dict) -> list[str]:
    """Flag any withholding drag on the recommended allocation."""
    notes = []
    for a in allocations:
        ticker = a["ticker"]
        rate = targets.get(ticker, {}).get("withholding_rate", 0.0)
        yield_approx = targets.get(ticker, {}).get("dividend_yield_approx", 0.0)
        if rate > 0 and yield_approx > 0:
            annual_income = a["amount_usd"] * (yield_approx / 100)
            annual_drag = annual_income * rate
            notes.append(
                f"  {ticker}: ${a['amount_usd']:,.0f} × {yield_approx:.1f}% yield × {int(rate*100)}% withholding "
                f"≈ ${annual_drag:.0f}/yr in withheld distributions"
            )
    return notes


# ── Printers ─────────────────────────────────────────────────────────────────

def print_report(result: dict, targets: dict):
    if "error" in result:
        print(f"\n⚠️  {result['error']}")
        return

    allocs = result["allocations"]
    total_alloc = result["total_allocated"]

    print(f"\n{'═'*62}")
    print(f"  CONTRIBUTION ALLOCATION REPORT — {result['report_date']}")
    print(f"{'═'*62}")
    print(f"  Portfolio value before:  ${result['portfolio_value']:>12,.2f}")
    print(f"  Contribution:            ${result['contribution']:>12,.2f}")
    print(f"  Portfolio value after:   ${result['new_total']:>12,.2f}")
    print(f"{'─'*62}")

    print(f"\n  {'Ticker':<7} {'$Amount':>10} {'~Shares':>9} {'Price':>8} {'Curr%':>7} {'Tgt%':>6} {'Drift':>7}")
    print(f"  {'─'*7} {'─'*10} {'─'*9} {'─'*8} {'─'*7} {'─'*6} {'─'*7}")
    for a in allocs:
        print(
            f"  {a['ticker']:<7} ${a['amount_usd']:>9,.2f} {a['shares_approx']:>9g} "
            f"${a['current_price']:>7.2f} {a['current_pct']:>6.1f}% {a['target_pct']:>5.1f}% "
            f"{a['drift']:>+6.1f}%"
        )
    print(f"  {'─'*7} {'─'*10}")
    print(f"  {'TOTAL':<7} ${total_alloc:>9,.2f}")
    if result.get("leftover_cash"):
        print(f"  Unallocated cash remainder (whole-share rounding): ${result['leftover_cash']:,.2f}")

    print(f"\n{'─'*62}")
    print(f"  ORDER LIST — ready for TradeStation")
    print(f"{'─'*62}")
    print(f"  Timing: 9:30–10:00 ET | Order type: LIMIT at ask + 0.05%\n")
    for i, a in enumerate(allocs, 1):
        if a["shares_approx"] > 0 and a["current_price"] > 0:
            limit_price = round(a["current_price"] * 1.0005, 2)
            print(
                f"  {i}. BUY {a['ticker']:<5} {a['shares_approx']:g} shares  "
                f"LIMIT ${limit_price:.2f}   (~${a['amount_usd']:,.0f})"
            )

    print(f"\n{'─'*62}")
    print(f"  NRA TAX IMPACT OF THIS ALLOCATION")
    print(f"{'─'*62}")
    notes = tax_advisory(allocs, targets)
    if notes:
        for note in notes:
            print(note)
    else:
        print("  No withholding drag on this allocation. ✅")

    print(f"\n{'═'*62}\n")


def print_json(result: dict):
    print(json.dumps(result, indent=2, default=str))


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Optimal contribution allocator")
    parser.add_argument("--amount", type=float, required=True, help="Contribution amount in USD")
    parser.add_argument("--positions", default=str(POSITIONS_FILE), help="Path to positions.csv")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of report")
    args = parser.parse_args()

    if args.amount <= 0:
        print("ERROR: --amount must be positive", file=sys.stderr)
        sys.exit(1)

    positions = load_positions(Path(args.positions))
    targets = load_targets(TARGET_FILE)
    config = load_config(CONFIG_FILE)

    result = compute_allocation(positions, targets, args.amount, config)

    if args.json:
        print_json(result)
    else:
        print_report(result, targets)


if __name__ == "__main__":
    main()
