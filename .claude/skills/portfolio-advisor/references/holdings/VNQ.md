---
ticker: VNQ
name: Vanguard Real Estate ETF
last_reviewed: 2026-05-11
source: target_allocation.yaml, tax_rules_nra_dr.md
---

# VNQ — Vanguard Real Estate ETF

## Key facts

| Field | Value |
|---|---|
| Issuer | Vanguard |
| Structure | ETF |
| Expense ratio | 0.12% |
| Benchmark | MSCI US Investable Market Real Estate 25/50 Index |
| Management style | Passive index |
| Holdings | ~160 US REITs and real estate companies |
| Dividend yield (approx) | ~4.0% |
| Duration / rate sensitivity | High (acts like long-duration bonds in rate environments) |

## What it holds

US Real Estate Investment Trusts (REITs) across all subsectors: retail, residential, industrial, office, healthcare, data centers, cell towers. Top holdings: Prologis, American Tower, Equinix, Welltower, Simon Property Group, Digital Realty.

Sector exposure (REIT subtypes, approximate):
- Industrial / logistics: ~15%
- Data centers / cell towers: ~20%
- Healthcare: ~12%
- Residential: ~12%
- Retail: ~10%
- Diversified: ~10%
- Other: ~21%

## NRA tax treatment

| Income type | Rate | Notes |
|---|---|---|
| REIT distributions | **30% withheld** | REIT income treated as ordinary dividends for NRA withholding |
| Capital gains on shares | **0%** (generally) | NRA exemption applies to ETF share sales |
| FIRPTA on sale | Generally **not triggered** | Publicly traded REIT ETF shares held by diversified investors typically exempt; verify with tax advisor if selling a large position |
| Net yield after withholding | **~2.8%** | (~4.0% × 0.70) |

**Annual withholding cost (at 7% target, ~$70K position on $1M portfolio):** ~$840/year withheld on distributions.

**Treat VNQ as a diversification tool, not an income tool.** The real estate exposure and low correlation to bonds justifies inclusion, but the 30% withholding makes it expensive for income generation.

## IPS role

| Field | Value |
|---|---|
| Target allocation | 7% |
| Max allowed (IPS constraint) | 10% |
| Asset class | Real Assets / REITs |
| Rebalancing bands | ±3% soft, ±5% hard |
| Rationale | Real asset diversification, inflation sensitivity, low correlation to fixed income |

## Key risks

- **Interest rate risk:** REITs are highly sensitive to rate increases (rising rates increase cap rates → property values fall)
- **Tax drag:** 30% withholding on all distributions — highest per-dollar tax cost in portfolio after VCIT for NRA
- **FIRPTA:** Applicable to direct REIT ownership; generally not triggered for ETF holders, but verify before any large sale

## Annual review checklist

- [ ] Confirm VNQ weight ≤ 10% (IPS constraint) — flag immediately if breached
- [ ] Review FIRPTA guidance if considering selling shares (consult tax advisor for large sales)
- [ ] Do not increase allocation above 7% target for income purposes — tax drag does not justify overweighting
