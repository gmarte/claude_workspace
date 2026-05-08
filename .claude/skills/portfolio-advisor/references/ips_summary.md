# Investment Policy Statement — Condensed Reference
**Investor:** Giancarlo Marte | **Last reviewed:** May 2026

---

## Core mandate

Build a low-cost, diversified, tax-aware ETF portfolio on TradeStation that compounds over 20+ years toward $10,000/month in passive income (inflation-adjusted). Never sacrifice long-term discipline for short-term market noise.

---

## Investor snapshot

| Parameter | Value |
|---|---|
| Age | 43 |
| Time horizon | 20+ years |
| Tax residency | Dominican Republic (NRA, no US treaty) |
| Account | Individual Equities Margin — TradeStation US |
| Risk: emotional | Low (avoid large drawdowns) |
| Risk: capacity | Moderate (long horizon absorbs volatility) |
| Quarterly contribution | $3,100 |
| Crypto | Held separately — excluded from this IPS |

---

## Target allocation

| ETF | Name | Target % | Asset class | Withholding |
|---|---|---|---|---|
| VTI | US Total Market | 25% | US Equity | 30% on divs |
| VEA | Developed Intl | 18% | Intl Equity | 30% on divs |
| VWO | Emerging Markets | 9% | EM Equity | 30% on divs |
| SGOV | 0-3mo Treasuries | 8% | Gov Fixed Income | 0% |
| SHY | 1-3yr Treasuries | 5% | Gov Fixed Income | 0% |
| VCIT | Corp Bonds Interm | 10% | Corp Fixed Income | 30% on interest |
| SCHP | US TIPS | 8% | Inflation-Protected | 0% |
| VNQ | US REITs | 7% | Real Estate | 30% on distributions |
| PDBC | Commodities | 5% | Commodities | 0% (C-corp structure) |
| CASH | Operating reserve | 5% | Cash | N/A |

**Total: 100%**

---

## Rebalancing rules

- **Method:** New money only — never sell to rebalance.
- **Soft trigger:** Drift > ±3% from target → prioritize on next contribution.
- **Hard limit:** Drift > ±5% from target → must address on next contribution.
- **Frequency:** Review quarterly (Jan, Apr, Jul, Oct), or when triggered by ±3% drift.

---

## Constraint checklist

| Constraint | Limit |
|---|---|
| Max single ETF weight | 25% |
| Max GICS sector (look-through) | 20% |
| Max single-stock indirect exposure | 5% |
| Total equity ceiling | 70% |
| Total fixed income floor | 20% |
| International equity (VEA + VWO) | ≥25% |
| REIT allocation ceiling | 10% (tax drag management) |
| Commodities ceiling | 8% |

---

## Contribution protocol

1. Determine amount (default $3,100; adjust if needed).
2. Run `/portfolio-advisor` to get current drift analysis.
3. Deploy new money to the most underweight positions first.
4. If VIX > 30, split contribution into 4 equal weekly tranches.
5. Use LIMIT orders, placed during 9:30–10:00 ET.
6. Update `positions.csv` after each trade.

---

## What this IPS does NOT allow

- Selling positions for tactical rebalancing or market-timing.
- Investing in individual stocks (ETFs only — no single-stock picks).
- Leveraged or inverse ETFs.
- Options or derivatives.
- Deviating from the allocation table based on short-term market views.
- Adding to overweight positions (even if the thesis is compelling).

---

## Tactical tilt allowance

Within the ±3%/±5% bands, minor tilts are permitted:

- **Macro: rising rates** → tilt toward SGOV/SHY over VCIT (shorter duration).
- **Macro: high inflation** → tilt toward SCHP when due for contribution.
- **Tax: DOP weakening** → no direct action (USD-denominated portfolio, natural hedge).
- **High volatility (VIX > 30)** → tranche contribution; don't change allocation targets.

No tilt may push any position outside its hard limit.

---

## Income projection (approximate)

| Portfolio size | Blended yield* | Gross annual | Net after 30% WHT |
|---|---|---|---|
| $250,000 | ~2.5% | ~$6,250 | ~$4,375 |
| $500,000 | ~2.5% | ~$12,500 | ~$8,750 |
| $1,000,000 | ~2.5% | ~$25,000 | ~$17,500 |
| $3,000,000 | ~2.5% | ~$75,000 | ~$52,500 |

*Blended yield accounts for zero-yield positions (PDBC, growth tilt in VTI).
To reach $10K/month net ≈ $120K/year net: need ~$3M+ at current blended yield after withholding.
Capital appreciation (0% WHT) is the primary return driver for this investor — not income.

---

## Review cadence

| Trigger | Action |
|---|---|
| Quarterly (Jan/Apr/Jul/Oct) | Contribution + full review |
| Any position drifts > 3% | Prioritize on next contribution |
| Any position drifts > 5% | Flag — must address immediately |
| VIX > 30 | Tranche contribution; no other changes |
| Fed rate change | Review SGOV/SHY/VCIT duration |
| Annual | Update ETF metadata, GICS weights, model IDs in CLAUDE.md |
