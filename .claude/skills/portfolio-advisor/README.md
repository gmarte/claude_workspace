# portfolio-advisor — activation guide

Personal AI financial agent for Giancarlo's long-term ETF portfolio on TradeStation.

---

## How Claude Code skills work

Skills are instruction files that Claude Code reads automatically when you are working inside this repo. When you say something that matches the skill's trigger phrases, Claude loads `SKILL.md` and executes the full workflow — no slash command needed, no copy-pasting your profile.

**Requirement:** You must be running Claude Code with this repo as your working directory (`c:\TEMP\claude_workspace`). The skill is project-local and only activates inside this workspace.

---

## Step 1 — One-time setup

### 1a. Install the dependency

The Python scripts require PyYAML. Using the repo's virtual environment:

```bash
# From the workspace root
venv\Scripts\python.exe -m pip install pyyaml

# Verify
venv\Scripts\python.exe -c "import yaml; print('pyyaml OK')"
```

### 1b. Fill in your positions

Open [positions.csv](.claude/skills/portfolio-advisor/positions.csv) and replace the template zeros with your real holdings. Update this file after every trade.

```
ticker,shares,avg_cost,last_price,last_updated
VTI,42.500,210.50,238.75,2026-05-01
VEA,65.000,46.20,51.30,2026-05-01
VWO,28.000,41.10,45.80,2026-05-01
SGOV,80.000,100.05,100.12,2026-05-01
SHY,35.000,82.30,83.10,2026-05-01
VCIT,55.000,78.20,80.45,2026-05-01
SCHP,48.000,52.10,54.30,2026-05-01
VNQ,22.000,88.50,92.00,2026-05-01
PDBC,40.000,14.20,15.80,2026-05-01
```

> **last_price** — enter the closing price from your last TradeStation session.
> **last_updated** — use `YYYY-MM-DD` format. The skill flags prices older than 1 trading day.

### 1c. Review your profile (optional)

[portfolio_config.yaml](.claude/skills/portfolio-advisor/portfolio_config.yaml) contains your fixed investor profile (age, tax status, quarterly contribution, constraints). It comes pre-filled. Edit only if something changes — for example, updating `quarterly_amount` or `age`.

---

## Step 2 — Activate the skill

Open Claude Code in this workspace and say any of the following. Claude will detect the context and run the full 6-step workflow automatically.

### Trigger phrases

| What you say | What happens |
|---|---|
| "Let's check the market" | Full report with market snapshot + portfolio status |
| "I'm thinking of investing $3,100 today" | Full report + contribution recommendation for that amount |
| "Time for my quarterly contribution" | Full report using the default $3,100 quarterly amount |
| "Should I rebalance?" | Drift analysis + compliance check + recommendation |
| "Run my portfolio check" | Complete sections A–G |
| "What's the market doing for my positions?" | Market snapshot focused on your ETFs |
| "Investing $500 this week" | Recommendation for non-standard contribution amount |

Any message containing your ETF tickers (VTI, VEA, VWO, etc.), the word "contribution," "rebalance," or "TradeStation" in an investment context will also trigger the skill.

### What Claude will do

When triggered, Claude executes this workflow in order:

```
1. Load your investor profile from portfolio_config.yaml
2. Read your current positions from positions.csv
3. Fetch live prices via web search for each ETF
4. Fetch market context: S&P 500, Nasdaq, 10Y Treasury, VIX, sector performance
5. Run diversification analysis: drift table, compliance checklist, sector look-through
6. Calculate optimal contribution allocation (gap-closing algorithm)
7. Deliver the full report — sections A through G
```

The report covers:
- **A** — Market snapshot (indices, rates, VIX, geopolitical flags)
- **B** — Your portfolio status (drift table for all positions)
- **C** — Diversification compliance (IPS rules pass/fail)
- **D** — Contribution recommendation (dollar amounts per ETF)
- **E** — Order list ready for TradeStation
- **F** — Risk flags (VIX alerts, overweight positions, tax drag)
- **G** — Next quarterly reminder

---

## Step 3 — After each trade

Update [positions.csv](.claude/skills/portfolio-advisor/positions.csv) with your new share counts, updated average cost, current price, and today's date. This is the only manual maintenance the skill requires between sessions.

---

## Running the scripts directly (optional)

You can run the Python scripts outside of Claude for testing or standalone analysis:

```bash
# Diversification check (requires updated positions.csv)
venv\Scripts\python.exe .claude\skills\portfolio-advisor\scripts\check_diversification.py

# Contribution allocator
venv\Scripts\python.exe .claude\skills\portfolio-advisor\scripts\allocate_contribution.py --amount 3100

# Full report (market section A will show placeholders — Claude fills it via web search)
venv\Scripts\python.exe .claude\skills\portfolio-advisor\scripts\format_report.py --amount 3100

# JSON output (useful for piping or logging)
venv\Scripts\python.exe .claude\skills\portfolio-advisor\scripts\check_diversification.py --json
```

---

## Maintenance schedule

| Frequency | Action |
|---|---|
| After every trade | Update `positions.csv` — shares, avg_cost, last_price, last_updated |
| Every quarter (Jan/Apr/Jul/Oct) | Trigger the skill for your contribution run |
| Annually | Update ETF GICS weights and top holdings in `target_allocation.yaml` (use Vanguard/iShares fund fact sheets) |
| Annually | Update yield estimates for SGOV/SHY in `target_allocation.yaml` (tracks Fed rate) |
| Every 3 years | Renew W-8BEN with TradeStation |
| When you turn 44, 45, etc. | Update `age` in `portfolio_config.yaml` |

---

## File reference

```
.claude/skills/portfolio-advisor/
├── SKILL.md                      ← Claude reads this when the skill triggers
├── portfolio_config.yaml         ← Your investor profile (age, tax, constraints)
├── positions.csv                 ← ⭐ Update after every trade
├── target_allocation.yaml        ← IPS target weights + ETF metadata
├── requirements.txt              ← pyyaml
├── scripts/
│   ├── check_diversification.py  ← Drift analysis + compliance check
│   ├── allocate_contribution.py  ← Gap-closing contribution allocator
│   └── format_report.py          ← Full report assembler (sections A–G)
└── references/
    ├── ips_summary.md            ← Your condensed IPS for quick reference
    └── tax_rules_nra_dr.md       ← NRA / Dominican Republic tax treatment
```

---

## Troubleshooting

**Skill doesn't trigger**
Make sure you are running Claude Code from `c:\TEMP\claude_workspace`. Project-local skills only load when Claude is opened in that directory.

**"PyYAML is required" error**
Run `venv\Scripts\python.exe -m pip install pyyaml` from the workspace root.

**"All positions have zero value" error**
Your `positions.csv` still has the template zeros. Fill in real share counts and prices.

**Stale price warning**
The skill flags `last_price` values older than 1 trading day. Update the `last_price` and `last_updated` columns in `positions.csv` before running.

**Script path not found**
Run scripts from the workspace root (`c:\TEMP\claude_workspace`), not from inside the skill folder.
