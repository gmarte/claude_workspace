# portfolio-advisor skill

Personal AI financial agent for Giancarlo's long-term ETF portfolio on TradeStation.

## How to trigger

Say any of these phrases in your Claude Code workspace:

- "Let's check the market"
- "I'm thinking of investing $2,500 today"
- "Time for my quarterly contribution"
- "Should I rebalance?"
- "Run my portfolio check"

Claude will execute the full 6-step workflow: load your profile → fetch live prices → market research → diversification check → contribution recommendation → full report.

## Setup

1. Install the single dependency:
   ```bash
   pip install pyyaml
   ```

2. Update `positions.csv` with your actual holdings after every trade:
   ```
   ticker,shares,avg_cost,last_price,last_updated
   VTI,42.500,210.50,238.75,2026-05-01
   VEA,65.000,46.20,51.30,2026-05-01
   ...
   ```

3. Review `portfolio_config.yaml` — update `age` and `quarterly_amount` as needed.

4. Review `target_allocation.yaml` — update GICS weights and top holdings annually (Vanguard publishes updated fund fact sheets).

## Running scripts standalone

```bash
# Full diversification report
python .claude/skills/portfolio-advisor/scripts/check_diversification.py

# Contribution allocator
python .claude/skills/portfolio-advisor/scripts/allocate_contribution.py --amount 3100

# Full assembled report (requires market data or shows placeholders for section A)
python .claude/skills/portfolio-advisor/scripts/format_report.py --amount 3100
```

## File structure

```
.claude/skills/portfolio-advisor/
├── SKILL.md                        ← skill definition (Claude reads this)
├── portfolio_config.yaml           ← your fixed investor profile
├── positions.csv                   ← your current holdings (update after trades)
├── target_allocation.yaml          ← IPS target weights + ETF metadata
├── requirements.txt                ← pip install pyyaml
├── scripts/
│   ├── check_diversification.py   ← drift analysis + compliance check
│   ├── allocate_contribution.py   ← optimal contribution split
│   └── format_report.py           ← full report assembler (sections A–G)
└── references/
    ├── ips_summary.md             ← condensed IPS for quick reference
    └── tax_rules_nra_dr.md        ← NRA / Dominican Republic tax rules
```

## Maintenance

| When | What to update |
|---|---|
| After every trade | `positions.csv` — shares, avg_cost, last_price, last_updated |
| Every quarter | Run the skill for contribution + review |
| Annually | ETF GICS weights and top holdings in `target_allocation.yaml` |
| Every 3 years | W-8BEN with TradeStation |
| When Fed moves rates | SGOV/SHY yield estimates in `target_allocation.yaml` |
