# Claude Workspace — Giancarlo Marte

Personal Claude Code workspace for automating daily tasks (personal and work).

## Owner

- **GitHub:** gmarte
- **Email:** giancarlo.marte@gmail.com

## Purpose

This repo is a living workspace. Each subfolder is an automation project. We ship working scripts, not prototypes — every project should be runnable end-to-end.

## Workspace Structure

```
/automations/       # Automation projects (one subfolder per project)
/shared/            # Reusable utilities shared across projects
```

## Guiding Principles

- **Working code over scaffolding.** Every project must be runnable before it's considered done.
- **Stay current.** Use the latest stable Claude models (currently `claude-sonnet-4-6`; Opus `claude-opus-4-7` for heavy reasoning). Check model IDs in CLAUDE.md if unsure.
- **Prompt caching by default.** All Claude API calls must use prompt caching (`cache_control`) to minimize cost.
- **Secrets out of code.** API keys and credentials go in `.env` files (gitignored), never hardcoded.
- **Minimal dependencies.** Prefer standard library + one well-chosen package over a stack of packages.
- **No placeholder TODOs shipped.** If a feature isn't implemented, it isn't committed.

## Current Claude Model IDs (as of May 2026)

| Model | ID |
|---|---|
| Sonnet 4.6 (default) | `claude-sonnet-4-6` |
| Opus 4.7 (heavy reasoning) | `claude-opus-4-7` |
| Haiku 4.5 (fast/cheap) | `claude-haiku-4-5-20251001` |

Update this table whenever a new model family ships.

## Environment

- **Platform:** Windows 11 (shell: bash via Claude Code, PowerShell also available)
- **Primary language:** Python (unless a project calls for something else)
- **Secrets:** `.env` files per project, loaded via `python-dotenv`

## Adding a New Automation Project

1. Create `/automations/<project-name>/`
2. Add a `README.md` with: what it does, how to run it, required env vars
3. Add a `.env.example` listing required secrets (no real values)
4. Make it runnable: `python main.py` or equivalent should work out of the box

## Git Hygiene

- Commit per working milestone, not per file save
- Branch per project: `feat/<project-name>`
- Never commit `.env` files (enforced by `.gitignore`)
