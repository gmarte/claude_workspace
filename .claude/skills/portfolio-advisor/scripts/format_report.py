"""
format_report.py
Assembles the full Portfolio Advisor report by calling check_diversification
and allocate_contribution as modules, then printing sections A–G.

Usage:
    python format_report.py --amount 3100
    python format_report.py --amount 3100 --positions path/to/positions.csv

Requires:
    check_diversification.py and allocate_contribution.py in the same directory.
    Market data (sections A) must be provided via --market-json or entered manually.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import date, datetime

# Allow importing sibling scripts
sys.path.insert(0, str(Path(__file__).parent))

try:
    import yaml
    def load_yaml(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
except ImportError:
    def load_yaml(path):
        raise SystemExit("PyYAML is required: pip install pyyaml")

import check_diversification as cd
import allocate_contribution as ac

SKILL_DIR = Path(__file__).resolve().parent.parent
POSITIONS_FILE = SKILL_DIR / "positions.csv"
TARGET_FILE = SKILL_DIR / "target_allocation.yaml"
CONFIG_FILE = SKILL_DIR / "portfolio_config.yaml"

DIVIDER = "═" * 65
SECTION = "━" * 65


# ── Market data placeholder ───────────────────────────────────────────────────

MARKET_TEMPLATE = {
    "date": str(date.today()),
    "sp500":       {"level": "N/A", "day_pct": "N/A", "mtd_pct": "N/A"},
    "nasdaq":      {"level": "N/A", "day_pct": "N/A", "mtd_pct": "N/A"},
    "russell2000": {"level": "N/A", "day_pct": "N/A", "mtd_pct": "N/A"},
    "treasury_10y": "N/A",
    "fed_funds":    "N/A",
    "vix":          "N/A",
    "mood":         "Market data not loaded — run web_search steps in SKILL.md.",
    "geo_flags":    ["(fetch via web_search)"],
    "sector_leaders":  ["(fetch via web_search)"],
    "sector_laggards": ["(fetch via web_search)"],
    "sources":      [],
}


def load_market_data(path: str | None) -> dict:
    if path and Path(path).exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return MARKET_TEMPLATE


# ── Section renderers ─────────────────────────────────────────────────────────

def section_a(market: dict) -> str:
    sp = market["sp500"]
    nq = market["nasdaq"]
    ru = market["russell2000"]
    vix = float(market["vix"]) if market["vix"] not in ("N/A", None) else None
    vix_str = f"{vix:.1f}" if vix is not None else "N/A"
    vix_note = ""
    if vix is not None:
        if vix > 30:
            vix_note = " 🚨 HIGH — consider tranching contribution"
        elif vix > 20:
            vix_note = " ⚠️  ELEVATED"
        else:
            vix_note = " ✅ NORMAL"

    geo = "\n".join(f"  • {e}" for e in market.get("geo_flags", []))
    leaders = ", ".join(market.get("sector_leaders", []))
    laggards = ", ".join(market.get("sector_laggards", []))
    sources = " | ".join(market.get("sources", ["(no sources provided)"]))

    return f"""
{SECTION}
  A. MARKET SNAPSHOT — {market['date']}
{SECTION}

  INDICES
    S&P 500       {sp['level']:>10}   Day: {sp['day_pct']:>8}   MTD: {sp['mtd_pct']:>8}
    Nasdaq        {nq['level']:>10}   Day: {nq['day_pct']:>8}   MTD: {nq['mtd_pct']:>8}
    Russell 2000  {ru['level']:>10}   Day: {ru['day_pct']:>8}   MTD: {ru['mtd_pct']:>8}

  RATES & VOLATILITY
    10Y Treasury: {market['treasury_10y']}   |   Fed Funds: {market['fed_funds']}   |   VIX: {vix_str}{vix_note}

  MARKET MOOD: {market['mood']}

  GEOPOLITICAL FLAGS:
{geo}

  SECTOR LEADERS:  {leaders}
  SECTOR LAGGARDS: {laggards}

  Sources: {sources}
"""


def section_b(portfolio: dict, targets: dict) -> str:
    total = portfolio["total_value"]
    rows = portfolio["rows"]
    soft_flags, hard_flags = cd.get_drift_flags(portfolio)

    lines = [
        f"\n{SECTION}",
        f"  B. PORTFOLIO STATUS",
        f"{SECTION}",
        f"\n  Total portfolio value: ${total:,.2f}",
        f"",
        f"  {'Ticker':<7} {'Shares':>8} {'Price':>8} {'Value':>11} {'Curr%':>7} {'Tgt%':>6} {'Drift':>7}  Action",
        f"  {'─'*7} {'─'*8} {'─'*8} {'─'*11} {'─'*7} {'─'*6} {'─'*7}  {'─'*18}",
    ]
    for r in sorted(rows, key=lambda x: targets.get(x["ticker"], {}).get("target_pct", 0), reverse=True):
        drift_icon = "🚨" if abs(r["drift"]) > cd.HARD_BAND else ("⚠️ " if abs(r["drift"]) > cd.SOFT_BAND else "  ")
        lines.append(
            f"  {r['ticker']:<7} {r['shares']:>8.3f} ${r['last_price']:>7.2f} "
            f"${r['value']:>10,.2f} {r['current_pct']:>6.1f}% {r['target_pct']:>5.1f}% "
            f"{r['drift']:>+6.1f}%  {drift_icon}{r['action']}"
        )
    lines += [
        f"  {'─'*7} {'─'*8} {'─'*8} {'─'*11} {'─'*7} {'─'*6}",
        f"  {'TOTAL':<7} {'':>8} {'':>8} ${total:>10,.2f} {'100.0%':>7} {'100.0%':>6}",
    ]

    if hard_flags:
        lines.append(f"\n  🚨 HARD BREACH — ACTION REQUIRED:")
        for r in hard_flags:
            lines.append(f"     {r['ticker']}: {r['drift']:+.1f}% from {r['target_pct']:.1f}% target")
    elif soft_flags:
        lines.append(f"\n  ⚠️  Soft flags (prioritize on this contribution):")
        for r in soft_flags:
            lines.append(f"     {r['ticker']}: {r['drift']:+.1f}% from {r['target_pct']:.1f}% target")
    else:
        lines.append(f"\n  ✅ All positions within ±{cd.SOFT_BAND}% soft band.")

    return "\n".join(lines)


def section_c(portfolio: dict, targets: dict, config: dict) -> str:
    compliance = cd.run_compliance(portfolio, targets, config)
    all_pass = all(c["pass"] for c in compliance)

    lines = [
        f"\n{SECTION}",
        f"  C. DIVERSIFICATION COMPLIANCE",
        f"{SECTION}",
        f"",
        f"  {'Rule':<52} {'Limit':<12} {'Actual':<10} Status",
        f"  {'─'*52} {'─'*12} {'─'*10} {'─'*6}",
    ]
    for c in compliance:
        icon = "✅" if c["pass"] else "❌"
        lines.append(f"  {icon} {c['rule']:<50} {c['limit']:<12} {c['actual']:<10}")

    ips_line = "✅ FULLY COMPLIANT" if all_pass else "❌ COMPLIANCE ISSUES — see above"
    lines += ["", f"  IPS STATUS: {ips_line}"]
    return "\n".join(lines)


def section_d(result: dict, targets: dict) -> str:
    if "error" in result:
        return f"\n{SECTION}\n  D. CONTRIBUTION RECOMMENDATION\n{SECTION}\n\n  ⚠️  {result['error']}\n"

    allocs = result["allocations"]
    lines = [
        f"\n{SECTION}",
        f"  D. CONTRIBUTION RECOMMENDATION — ${result['contribution']:,.0f}",
        f"{SECTION}",
        f"",
        f"  Portfolio before: ${result['portfolio_value']:,.2f}  →  After: ${result['new_total']:,.2f}",
        f"",
        f"  {'Ticker':<7} {'$Amount':>10} {'~Shares':>9} {'Price':>8} {'Curr%':>7} {'Tgt%':>6} {'Drift':>7}",
        f"  {'─'*7} {'─'*10} {'─'*9} {'─'*8} {'─'*7} {'─'*6} {'─'*7}",
    ]
    for a in allocs:
        lines.append(
            f"  {a['ticker']:<7} ${a['amount_usd']:>9,.2f} {a['shares_approx']:>9g} "
            f"${a['current_price']:>7.2f} {a['current_pct']:>6.1f}% {a['target_pct']:>5.1f}% "
            f"{a['drift']:>+6.1f}%"
        )
    lines += [
        f"  {'─'*7} {'─'*10}",
        f"  {'TOTAL':<7} ${result['total_allocated']:>9,.2f}",
    ]

    # Tax note
    tax_notes = ac.tax_advisory(allocs, targets)
    if tax_notes:
        lines += ["", "  NRA withholding drag on this allocation:"]
        lines.extend(tax_notes)

    return "\n".join(lines)


def section_e(result: dict) -> str:
    if "error" in result or not result.get("allocations"):
        return f"\n{SECTION}\n  E. ORDER LIST\n{SECTION}\n\n  No orders to place.\n"

    lines = [
        f"\n{SECTION}",
        f"  E. ORDER LIST — READY FOR TRADESTATION",
        f"{SECTION}",
        f"",
        f"  Timing:     9:30–10:00 ET (first 30 min for best ETF liquidity)",
        f"  Order type: LIMIT at ask + 0.05% buffer",
        f"  Account:    Individual Equities Margin — Abacus commission-free",
        f"",
    ]
    for i, a in enumerate(result["allocations"], 1):
        if a["shares_approx"] > 0 and a["current_price"] > 0:
            limit_price = round(a["current_price"] * 1.0005, 2)
            lines.append(
                f"  {i:>2}. BUY  {a['ticker']:<5}  {a['shares_approx']:g} shares  "
                f"LIMIT ${limit_price:.2f}   (~${a['amount_usd']:,.0f})"
            )
    lines += ["", f"  Total to deploy: ${result['total_allocated']:,.2f}"]
    if result.get("leftover_cash"):
        lines.append(f"  Cash remainder (whole-share rounding): ${result['leftover_cash']:,.2f}")
    lines.append("  Note: WHOLE shares only — TradeStation rejects fractional/decimal quantities.")
    return "\n".join(lines)


def section_f(portfolio: dict, targets: dict, market: dict) -> str:
    lines = [f"\n{SECTION}", f"  F. RISK FLAGS", f"{SECTION}", ""]

    flags = []
    vix = market.get("vix", "N/A")
    try:
        vix_val = float(vix)
        if vix_val > 30:
            flags.append(f"🚨 VIX = {vix_val:.1f} — ELEVATED VOLATILITY. Consider spreading "
                         f"the ${portfolio.get('contribution', 3100):,.0f} contribution over 4 weekly tranches.")
        elif vix_val > 20:
            flags.append(f"⚠️  VIX = {vix_val:.1f} — moderately elevated. Monitor for escalation.")
    except (ValueError, TypeError):
        pass

    _, hard_flags = cd.get_drift_flags(portfolio)
    for r in hard_flags:
        flags.append(f"🚨 HARD BREACH — {r['ticker']}: {r['drift']:+.1f}% from target. "
                     f"Prioritize on next contribution.")

    # VNQ tax drag estimate
    for row in portfolio["rows"]:
        if row["ticker"] == "VNQ" and row["value"] > 0:
            yield_approx = targets.get("VNQ", {}).get("dividend_yield_approx", 4.0)
            annual_income = row["value"] * (yield_approx / 100)
            drag = annual_income * 0.30
            flags.append(
                f"💸 VNQ TAX DRAG — Estimated ${drag:,.0f}/yr withheld at 30% "
                f"(${annual_income:,.0f} × 30% on ${row['value']:,.0f} position). "
                f"Keep allocation ≤7% target."
            )

    # PDBC year-end reminder
    if date.today().month in (11, 12):
        flags.append("📋 PDBC — Q4 reminder: confirm your broker's 1099 handling for this ETF. "
                     "PDBC is structured as a C-corp (no K-1), but verify annually.")

    if not flags:
        flags.append("✅ No significant risk flags today. Portfolio looks healthy.")

    lines.extend(f"  {f}" for f in flags)
    return "\n".join(lines)


def section_g(config: dict) -> str:
    today = date.today()
    typical_months = config.get("contributions", {}).get("typical_months", [1, 4, 7, 10])
    amount = config.get("contributions", {}).get("quarterly_amount", 3100)

    # Find next quarter month
    next_month = None
    for m in typical_months:
        if m > today.month or (m == today.month and today.day <= 7):
            next_month = m
            break
    if next_month is None:
        next_month = typical_months[0]
        next_year = today.year + 1
    else:
        next_year = today.year

    # YTD contributions estimate
    ytd_quarters = sum(1 for m in typical_months if m < today.month)
    ytd_total = ytd_quarters * amount

    return f"""
{SECTION}
  G. NEXT QUARTERLY REMINDER
{SECTION}

  Next contribution: First week of {datetime(next_year, next_month, 1).strftime('%B %Y')}
  Standard amount:   ${amount:,}
  Action:            Update positions.csv, then run /portfolio-advisor

  YTD contributions (estimated): ${ytd_total:,} across {ytd_quarters} tranche(s)
  Long-term goal:    ${config.get('investment_goals', {}).get('income_target_monthly', 10000):,}/month passive income
"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Full portfolio advisor report")
    parser.add_argument("--amount", type=float, default=3100, help="Contribution amount (default: 3100)")
    parser.add_argument("--positions", default=str(POSITIONS_FILE))
    parser.add_argument("--market-json", default=None, help="Path to market data JSON file")
    args = parser.parse_args()

    positions_path = Path(args.positions)
    positions = cd.load_positions(positions_path)
    targets = cd.load_targets(TARGET_FILE)
    config = cd.load_config(CONFIG_FILE)
    market = load_market_data(args.market_json)

    staleness = cd.check_staleness(positions)
    portfolio = cd.compute_portfolio(positions, targets)
    alloc_result = ac.compute_allocation(positions, targets, args.amount, config)

    now = datetime.now().strftime("%Y-%m-%d %H:%M ET")
    print(f"\n{DIVIDER}")
    print(f"  PORTFOLIO ADVISOR REPORT — {now}")
    print(DIVIDER)
    if staleness:
        print("\n⚠️  STALE PRICE WARNINGS:")
        for w in staleness:
            print(w)

    print(section_a(market))
    print(section_b(portfolio, targets))
    print(section_c(portfolio, targets, config))
    print(section_d(alloc_result, targets))
    print(section_e(alloc_result))
    print(section_f(portfolio, targets, market))
    print(section_g(config))

    print(DIVIDER)
    print("  END OF REPORT")
    print(DIVIDER + "\n")


if __name__ == "__main__":
    main()
