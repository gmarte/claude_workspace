"""
check_diversification.py
Reads positions.csv and target_allocation.yaml, then prints a full compliance
report: drift table, asset-class breakdown, sector look-through, and rule checks.

Usage:
    python check_diversification.py
    python check_diversification.py --positions path/to/positions.csv
    python check_diversification.py --json          # machine-readable output
"""

import csv
import sys
import json
import argparse
from pathlib import Path
from datetime import date, datetime

# ── Try to import yaml; fall back to a minimal inline parser for simple files ──
try:
    import yaml
    def load_yaml(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
except ImportError:
    def load_yaml(path):
        raise SystemExit(
            "PyYAML is required: pip install pyyaml\n"
            "Or run: pip install -r requirements.txt"
        )

SKILL_DIR = Path(__file__).resolve().parent.parent
POSITIONS_FILE = SKILL_DIR / "positions.csv"
TARGET_FILE = SKILL_DIR / "target_allocation.yaml"
CONFIG_FILE = SKILL_DIR / "portfolio_config.yaml"

SOFT_BAND = 3.0
HARD_BAND = 5.0
STALE_DAYS = 2


# ── Data loaders ──────────────────────────────────────────────────────────────

def load_positions(path: Path) -> list[dict]:
    if not path.exists():
        print(f"ERROR: positions file not found: {path}", file=sys.stderr)
        sys.exit(1)
    positions = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            positions.append({
                "ticker":       row["ticker"].strip().upper(),
                "shares":       float(row["shares"]),
                "avg_cost":     float(row["avg_cost"]),
                "last_price":   float(row["last_price"]),
                "last_updated": row["last_updated"].strip(),
                "value":        float(row["shares"]) * float(row["last_price"]),
            })
    return positions


def load_targets(path: Path) -> dict:
    data = load_yaml(path)
    return data.get("holdings", {})


def load_config(path: Path) -> dict:
    return load_yaml(path)


# ── Staleness check ───────────────────────────────────────────────────────────

def check_staleness(positions: list[dict]) -> list[str]:
    warnings = []
    today = date.today()
    for p in positions:
        try:
            updated = datetime.strptime(p["last_updated"], "%Y-%m-%d").date()
            delta = (today - updated).days
            if delta > STALE_DAYS:
                warnings.append(
                    f"  ⚠️  {p['ticker']}: last_price is {delta} days old ({p['last_updated']})"
                )
        except ValueError:
            warnings.append(f"  ⚠️  {p['ticker']}: unreadable date '{p['last_updated']}'")
    return warnings


# ── Portfolio calculations ────────────────────────────────────────────────────

def compute_portfolio(positions: list[dict], targets: dict) -> dict:
    total_value = sum(p["value"] for p in positions)
    if total_value == 0:
        print("ERROR: All positions have zero value. Update positions.csv with current prices.", file=sys.stderr)
        sys.exit(1)

    rows = []
    for p in positions:
        ticker = p["ticker"]
        current_pct = (p["value"] / total_value) * 100
        target_pct = targets.get(ticker, {}).get("target_pct", 0.0)
        drift = current_pct - target_pct
        action = "HOLD"
        if drift < -SOFT_BAND:
            action = "BUY (underweight)"
        elif drift > SOFT_BAND:
            action = "OVERWEIGHT — skip"
        rows.append({
            "ticker":      ticker,
            "shares":      p["shares"],
            "last_price":  p["last_price"],
            "value":       p["value"],
            "current_pct": current_pct,
            "target_pct":  target_pct,
            "drift":       drift,
            "action":      action,
            "avg_cost":    p["avg_cost"],
            "unrealized_pnl": (p["last_price"] - p["avg_cost"]) * p["shares"],
        })

    # Add any target positions not yet in portfolio
    held_tickers = {p["ticker"] for p in positions}
    for ticker, meta in targets.items():
        if ticker not in held_tickers and ticker != "CASH":
            rows.append({
                "ticker":      ticker,
                "shares":      0.0,
                "last_price":  0.0,
                "value":       0.0,
                "current_pct": 0.0,
                "target_pct":  meta.get("target_pct", 0.0),
                "drift":       -meta.get("target_pct", 0.0),
                "action":      "BUY (not yet held)",
                "avg_cost":    0.0,
                "unrealized_pnl": 0.0,
            })

    return {"total_value": total_value, "rows": rows}


# ── Asset-class breakdown ─────────────────────────────────────────────────────

def compute_asset_classes(portfolio: dict, targets: dict) -> dict:
    buckets: dict[str, float] = {}
    total = portfolio["total_value"]
    for row in portfolio["rows"]:
        ticker = row["ticker"]
        asset_class = targets.get(ticker, {}).get("asset_class", "Unknown")
        buckets[asset_class] = buckets.get(asset_class, 0.0) + row["value"]
    return {k: (v / total * 100) for k, v in buckets.items()}


# ── Sector look-through ───────────────────────────────────────────────────────

def compute_sector_exposure(portfolio: dict, targets: dict) -> dict:
    """Compute effective GICS sector exposure by looking through each ETF."""
    sector_totals: dict[str, float] = {}
    total = portfolio["total_value"]
    for row in portfolio["rows"]:
        ticker = row["ticker"]
        etf_value = row["value"]
        gics = targets.get(ticker, {}).get("gics_weights", {})
        for sector, weight in gics.items():
            sector_totals[sector] = sector_totals.get(sector, 0.0) + etf_value * weight
    return {k: (v / total * 100) for k, v in sector_totals.items()}


# ── Single-stock indirect exposure ───────────────────────────────────────────

def compute_stock_exposure(portfolio: dict, targets: dict) -> dict:
    """Compute indirect single-stock exposure through ETF top holdings."""
    stock_totals: dict[str, float] = {}
    total = portfolio["total_value"]
    for row in portfolio["rows"]:
        ticker = row["ticker"]
        etf_value = row["value"]
        top_holdings = targets.get(ticker, {}).get("top_holdings", {})
        for stock, weight in top_holdings.items():
            stock_totals[stock] = stock_totals.get(stock, 0.0) + etf_value * weight
    return {k: (v / total * 100) for k, v in sorted(stock_totals.items(), key=lambda x: -x[1])}


# ── Compliance rules ──────────────────────────────────────────────────────────

def run_compliance(portfolio: dict, targets: dict, config: dict) -> list[dict]:
    constraints = config.get("constraints", {})
    rows = portfolio["rows"]
    total = portfolio["total_value"]
    asset_classes = compute_asset_classes(portfolio, targets)
    sectors = compute_sector_exposure(portfolio, targets)
    stocks = compute_stock_exposure(portfolio, targets)

    results = []

    def check(rule, limit_str, actual_val, limit_val, higher_is_bad=True):
        actual_str = f"{actual_val:.1f}%"
        ok = actual_val <= limit_val if higher_is_bad else actual_val >= limit_val
        results.append({
            "rule": rule,
            "limit": limit_str,
            "actual": actual_str,
            "pass": ok,
        })

    # Max single ETF weight
    max_etf = max(r["current_pct"] for r in rows)
    max_etf_ticker = max(rows, key=lambda r: r["current_pct"])["ticker"]
    check(
        f"Max single ETF weight ({max_etf_ticker})",
        f"≤ {constraints.get('max_single_etf_pct', 25)}%",
        max_etf,
        constraints.get("max_single_etf_pct", 25.0),
    )

    # Equity ceiling
    equity = sum(
        v for k, v in asset_classes.items()
        if "Equity" in k or "equity" in k.lower()
    )
    check(
        "Total equity exposure",
        f"≤ {constraints.get('max_equity_pct', 70)}%",
        equity,
        constraints.get("max_equity_pct", 70.0),
    )

    # Fixed income floor
    fi = sum(v for k, v in asset_classes.items() if "Fixed Income" in k)
    check(
        "Total fixed income exposure",
        f"≥ {constraints.get('min_fixed_income_pct', 20)}%",
        fi,
        constraints.get("min_fixed_income_pct", 20.0),
        higher_is_bad=False,
    )

    # International equity floor (VEA + VWO)
    intl = sum(
        r["current_pct"] for r in rows
        if r["ticker"] in ("VEA", "VWO")
    )
    check(
        "International equity (VEA + VWO)",
        f"≥ {constraints.get('min_international_equity_pct', 25)}%",
        intl,
        constraints.get("min_international_equity_pct", 25.0),
        higher_is_bad=False,
    )

    # REIT ceiling
    reit = asset_classes.get("Real Estate", 0.0)
    check(
        "REIT allocation (30% withholding drag)",
        f"≤ {constraints.get('max_reit_pct', 10)}%",
        reit,
        constraints.get("max_reit_pct", 10.0),
    )

    # Sector concentration look-through
    if sectors:
        max_sector_name = max(sectors, key=sectors.get)
        max_sector_val = sectors[max_sector_name]
        check(
            f"Largest GICS sector look-through ({max_sector_name})",
            f"≤ {constraints.get('max_sector_pct', 20)}%",
            max_sector_val,
            constraints.get("max_sector_pct", 20.0),
        )

    # Single-stock indirect exposure
    if stocks:
        top_stock = next(iter(stocks))
        top_val = stocks[top_stock]
        check(
            f"Indirect single-stock exposure ({top_stock})",
            f"≤ {constraints.get('max_single_stock_indirect_pct', 5)}%",
            top_val,
            constraints.get("max_single_stock_indirect_pct", 5.0),
        )

    return results


# ── Drift summary ─────────────────────────────────────────────────────────────

def get_drift_flags(portfolio: dict) -> tuple[list, list]:
    soft, hard = [], []
    for row in portfolio["rows"]:
        d = abs(row["drift"])
        if d > HARD_BAND:
            hard.append(row)
        elif d > SOFT_BAND:
            soft.append(row)
    return soft, hard


# ── Printers ─────────────────────────────────────────────────────────────────

def print_report(portfolio: dict, targets: dict, config: dict, staleness: list[str]):
    total = portfolio["total_value"]
    rows = portfolio["rows"]
    asset_classes = compute_asset_classes(portfolio, targets)
    sectors = compute_sector_exposure(portfolio, targets)
    stocks = compute_stock_exposure(portfolio, targets)
    compliance = run_compliance(portfolio, targets, config)
    soft_flags, hard_flags = get_drift_flags(portfolio)

    print(f"\n{'═'*62}")
    print(f"  DIVERSIFICATION REPORT — {date.today()}")
    print(f"{'═'*62}")

    if staleness:
        print("\n⚠️  STALE PRICE WARNINGS:")
        for w in staleness:
            print(w)

    print(f"\nTotal portfolio value: ${total:,.2f}\n")

    # Drift table
    print(f"{'─'*62}")
    print(f"  POSITION DRIFT TABLE")
    print(f"{'─'*62}")
    header = f"{'Ticker':<8} {'Shares':>8} {'Price':>8} {'Value':>11} {'Curr%':>7} {'Tgt%':>6} {'Drift':>7} {'Action'}"
    print(header)
    print("─" * 80)
    for r in sorted(rows, key=lambda x: -abs(x["drift"])):
        drift_icon = ""
        if abs(r["drift"]) > HARD_BAND:
            drift_icon = "🚨"
        elif abs(r["drift"]) > SOFT_BAND:
            drift_icon = "⚠️ "
        print(
            f"{r['ticker']:<8} {r['shares']:>8.3f} {r['last_price']:>8.2f} "
            f"${r['value']:>10,.2f} {r['current_pct']:>6.1f}% {r['target_pct']:>5.1f}% "
            f"{r['drift']:>+6.1f}% {drift_icon}{r['action']}"
        )
    print("─" * 80)
    print(f"{'TOTAL':<8} {'':>8} {'':>8} ${total:>10,.2f} {'100.0%':>7} {'100.0%':>6}")

    # Soft / hard drift flags
    if hard_flags:
        print(f"\n🚨 HARD BREACH (>{HARD_BAND}% drift) — ACTION REQUIRED:")
        for r in hard_flags:
            print(f"   {r['ticker']}: {r['drift']:+.1f}% (target {r['target_pct']:.1f}%)")
    if soft_flags:
        print(f"\n⚠️  Soft flags (>{SOFT_BAND}% drift) — prioritize on next contribution:")
        for r in soft_flags:
            print(f"   {r['ticker']}: {r['drift']:+.1f}% (target {r['target_pct']:.1f}%)")
    if not soft_flags and not hard_flags:
        print("\n✅ All positions within ±3% soft band.")

    # Asset class breakdown
    print(f"\n{'─'*62}")
    print(f"  ASSET CLASS BREAKDOWN")
    print(f"{'─'*62}")
    for ac, pct in sorted(asset_classes.items(), key=lambda x: -x[1]):
        bar = "█" * int(pct / 2)
        print(f"  {ac:<40} {pct:5.1f}%  {bar}")

    # Top-5 sector look-through
    print(f"\n{'─'*62}")
    print(f"  GICS SECTOR LOOK-THROUGH (top 10)")
    print(f"{'─'*62}")
    for sector, pct in sorted(sectors.items(), key=lambda x: -x[1])[:10]:
        flag = " ⚠️" if pct > 20 else ""
        print(f"  {sector:<35} {pct:5.1f}%{flag}")

    # Top-5 indirect stock exposure
    print(f"\n{'─'*62}")
    print(f"  INDIRECT SINGLE-STOCK EXPOSURE (top 10)")
    print(f"{'─'*62}")
    for stock, pct in list(stocks.items())[:10]:
        flag = " 🚨" if pct > 5 else (" ⚠️" if pct > 3 else "")
        print(f"  {stock:<35} {pct:5.2f}%{flag}")

    # Compliance table
    print(f"\n{'─'*62}")
    print(f"  COMPLIANCE CHECKLIST")
    print(f"{'─'*62}")
    all_pass = True
    for c in compliance:
        icon = "✅" if c["pass"] else "❌"
        if not c["pass"]:
            all_pass = False
        print(f"  {icon} {c['rule']:<48} Limit: {c['limit']:<10} Actual: {c['actual']}")

    print(f"\n{'═'*62}")
    status = "✅ FULLY COMPLIANT" if all_pass else "❌ COMPLIANCE ISSUES FOUND — review above"
    print(f"  IPS STATUS: {status}")
    print(f"{'═'*62}\n")


def print_json(portfolio: dict, targets: dict, config: dict, staleness: list[str]):
    output = {
        "report_date": str(date.today()),
        "total_value": portfolio["total_value"],
        "stale_warnings": staleness,
        "positions": portfolio["rows"],
        "asset_classes": compute_asset_classes(portfolio, targets),
        "sector_exposure": compute_sector_exposure(portfolio, targets),
        "top_stock_exposure": dict(list(compute_stock_exposure(portfolio, targets).items())[:10]),
        "compliance": run_compliance(portfolio, targets, config),
    }
    print(json.dumps(output, indent=2, default=str))


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Portfolio diversification check")
    parser.add_argument("--positions", default=str(POSITIONS_FILE), help="Path to positions.csv")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of formatted report")
    args = parser.parse_args()

    positions = load_positions(Path(args.positions))
    targets = load_targets(TARGET_FILE)
    config = load_config(CONFIG_FILE)

    staleness = check_staleness(positions)
    portfolio = compute_portfolio(positions, targets)

    if args.json:
        print_json(portfolio, targets, config, staleness)
    else:
        print_report(portfolio, targets, config, staleness)


if __name__ == "__main__":
    main()
