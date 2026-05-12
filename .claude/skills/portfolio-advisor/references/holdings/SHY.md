---
ticker: SHY
name: iShares 1-3 Year Treasury Bond ETF
last_reviewed: 2026-05-11
source: target_allocation.yaml, tax_rules_nra_dr.md
---

# SHY — iShares 1-3 Year Treasury Bond ETF

## Key facts

| Field | Value |
|---|---|
| Issuer | BlackRock (iShares) |
| Structure | ETF |
| Expense ratio | 0.15% |
| Benchmark | ICE US Treasury 1-3 Year Bond Index |
| Management style | Passive index |
| Holdings | US Treasury notes (1-3 year maturity) |
| Dividend yield (approx) | ~4.5% (short end of yield curve) |
| Duration | ~1.8 years |

## What it holds

US Treasury notes and bonds with 1-3 years to maturity. Slightly longer duration than SGOV — more price sensitivity to rate changes but still low risk. Yield typically higher than T-bills when yield curve is normal; may be lower during inversion.

## NRA tax treatment

| Income type | Rate | Notes |
|---|---|---|
| Treasury interest | **0% withheld** | Portfolio interest exemption (IRC §871(h)) |
| Capital gains | **0%** | NRA exemption |
| Net yield | **~4.5%** | Full yield retained — no withholding drag |

Tax treatment identical to SGOV — both are pure US Treasury ETFs covered by the portfolio interest exemption.

## IPS role

| Field | Value |
|---|---|
| Target allocation | 5% |
| Asset class | Short-term Fixed Income |
| Rebalancing bands | ±3% soft, ±5% hard |
| Rationale | Tax-efficient fixed income with slightly longer duration than SGOV; yield curve positioning |

## SHY vs SGOV

| Factor | SGOV | SHY |
|---|---|---|
| Maturity | 0-3 months | 1-3 years |
| Duration | ~0.1 years | ~1.8 years |
| Rate sensitivity | Near zero | Low |
| Yield (current) | ~5.2% | ~4.5% |
| Withholding | 0% | 0% |
| Use case | Cash equivalent | Short-duration bond exposure |

When fixed income is underweight, prefer SGOV over SHY for new contributions (higher current yield, lower rate risk).

## Annual review checklist

- [ ] Update yield estimate in target_allocation.yaml when Fed changes rates
- [ ] Compare SHY yield vs SGOV — if curve steepens significantly, SHY becomes more attractive
- [ ] Confirm W-8BEN is current (same requirement as SGOV)
