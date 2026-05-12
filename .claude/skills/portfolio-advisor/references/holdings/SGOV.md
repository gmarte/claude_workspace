---
ticker: SGOV
name: iShares 0-3 Month Treasury Bond ETF
last_reviewed: 2026-05-11
source: target_allocation.yaml, tax_rules_nra_dr.md
---

# SGOV — iShares 0-3 Month Treasury Bond ETF

## Key facts

| Field | Value |
|---|---|
| Issuer | BlackRock (iShares) |
| Structure | ETF |
| Expense ratio | 0.09% |
| Benchmark | ICE 0-3 Month US Treasury Securities Index |
| Management style | Passive index |
| Holdings | US Treasury bills (0-3 month maturity) |
| Dividend yield (approx) | ~5.2% (tracks Fed Funds rate — update quarterly) |

## What it holds

Exclusively US Treasury bills maturing within 3 months. Near-zero duration — essentially a money market substitute with T-bill yield. Price stays extremely close to $100 NAV.

## NRA tax treatment

| Income type | Rate | Notes |
|---|---|---|
| Treasury interest | **0% withheld** | Portfolio interest exemption (IRC §871(h)) |
| Capital gains | **0%** | NRA exemption |
| Net yield | **~5.2%** | Full yield retained — no withholding drag at all |

**This is the most tax-efficient income position in the portfolio for an NRA.** SGOV currently yields more after withholding than VCIT (corporate bonds at 30% withholding), making it the preferred cash management instrument.

**Condition:** W-8BEN must be current with TradeStation. If it expires, backup withholding applies.

## IPS role

| Field | Value |
|---|---|
| Target allocation | 8% |
| Asset class | Short-term Fixed Income / Cash Equivalent |
| Rebalancing bands | ±3% soft, ±5% hard |
| Rationale | Liquidity reserve with maximum tax efficiency; preferred over money market funds |

## Yield tracking

SGOV yield closely tracks the Fed Funds rate (lagged ~1 quarter). Update `target_allocation.yaml` yield estimate when Fed changes rates materially (≥25 bps).

| Fed Funds rate | Approx SGOV yield |
|---|---|
| 5.25–5.50% | ~5.2% |
| 4.75–5.00% | ~4.7% |
| 4.25–4.50% | ~4.2% |

## Annual review checklist

- [ ] Update yield estimate in target_allocation.yaml quarterly (track Fed rate)
- [ ] Confirm W-8BEN is current with TradeStation (renew every 3 years)
- [ ] Compare SGOV yield vs VCIT after-withholding yield — flag if spread narrows below 0.5%
