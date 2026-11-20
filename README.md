# Per-user sandbox costs

Data, cost model, and measurement script behind the DigitalOcean article
**"One Sandbox Per User: Isolating AI Agents at Scale, and What Pause/Resume Changes"**
([ARTICLE URL]).

**Prices as of: November 19, 2026** · Current release: `v2026-11-19`

This repository lets you check every number in the article without taking our word for it:

- **Cost model:** what it costs to give 1,000 users their own sandbox on eight providers, at published list prices.
- **Price inputs:** every rate the model uses, with its source URL and capture date, as CSV and JSON.
- **Rebuild measurement:** the script, exact commands, and raw results for timing a fresh clone and dependency install.

> **Disclosure:** This repository is maintained by James Skelton, the article's author, who works at DigitalOcean. DigitalOcean Harness Runtime is one of the providers compared. Harness Runtime is in public preview; its features, pricing, and limits may change before general availability.

## Contents

```
.
├── README.md                          This file, including the changelog
├── LICENSE                            MIT (code in measurement/)
├── cost-model/
│   ├── README.md                      Assumptions, scenarios, and how to edit the model
│   ├── LICENSE                        CC BY 4.0 (model and data)
│   ├── per-user-sandbox-cost-model.xlsx
│   ├── price-inputs-2026-11-19.csv    Every rate, with source URL and capture date
│   ├── price-inputs-2026-11-19.json   Same data as JSON
│   └── provider-behavior-2026-11-19.csv  Isolation, idle defaults, and what survives a pause
└── measurement/
    ├── README.md                      Environment, exact commands, and results
    ├── measure_rebuild.py             Clone-and-install timing script
    ├── rebuild-test.yaml              Harness Runtime sandbox spec used for the run
    ├── requirements.txt
    └── results/
        ├── rebuild-results-2026-11-19.csv   Every run, not just medians
        └── measure-2026-11-19.log           Raw log from the run
```

## Results at a glance

Monthly cost of one sandbox per user, 1,000 users, default settings (20 sessions of 45 minutes per user per month, 2 vCPU / 4 GB, 25% CPU while working, 1.5 GB memory in use, 10 GB disk):

| Provider | Per user / month | What survives idle (default) |
|---|---|---|
| Fly.io Sprites | $1.08 | Files (memory only while warm) |
| Modal Sandboxes | $1.13 | Nothing |
| AWS AgentCore Runtime | $1.35 | Nothing |
| Cloudflare Sandbox | $1.58 | Nothing |
| DigitalOcean Harness Runtime | $1.59 | Processes, memory, and files |
| E2B | $2.91 | Nothing (default timeout action kills the sandbox) |
| Vercel Sandbox | $3.17 | Files |
| Daytona (container) | $3.71 | Files |

Fresh clone and dependency install on a Harness Runtime `mars-2vcpu-4gb` sandbox (median of 3 runs): Flask 5.8 s, Express 12.7 s, Fastify 23.0 s.

See `cost-model/README.md` for the best-configuration scenario, sensitivity tables, and all exclusions.

## How to verify or change the numbers

- **Check a price:** open `cost-model/price-inputs-2026-11-19.csv`, follow the `source_url`, and compare. Prices change; the capture date is on every row.
- **Change the assumptions:** open the `.xlsx` (or the Google Sheet copy, [SHEET COPY URL]) and edit the yellow cells on the **Inputs** sheet. Every result is a live formula.
- **Reproduce the rebuild timing:** follow `measurement/README.md`.

Found an error or an outdated price? Open an issue with the provider, the rate, and a link to the source.

## Versioning

Each release is tagged with the date its prices were checked, in the form `vYYYY-MM-DD`. A tag is a fixed "as of" snapshot; the `main` branch carries the latest data. The article links to the tag it was written against.

## Changelog

### v2026-11-19
- Initial release.
- List prices for eight providers captured November 19, 2026.
- DigitalOcean Harness Runtime modeled per its docs pricing page (last verified November 5, 2026): CPU on actual use, memory on allocation, session storage on capacity held. DigitalOcean's public pricing page describes an interim model (CPU at a flat 25% of allocated vCPUs, memory on peak use) that gives about $1.23 per user per month at defaults; this release uses the docs page because it gives the higher cost.
- Storage for DigitalOcean session storage and Vercel snapshots billed for the full month (running and paused), matching the Daytona convention.
- Rebuild timing measured on three public repositories (Flask, Express, Fastify) on a Harness Runtime `mars-2vcpu-4gb` sandbox in `ric1`.

### Planned
- If DigitalOcean confirms that the public pricing page's interim billing applies, set `G6` to 2 and `W6` to 0.25 on the **Rates** sheet, re-check all prices, regenerate the tables, and tag a new release.

## License

- Code in `measurement/` is licensed under the MIT License (see `LICENSE`).
- The cost model and data in `cost-model/` are licensed under Creative Commons Attribution 4.0 International (CC BY 4.0) (see `cost-model/LICENSE`).

Provider names and trademarks belong to their respective owners. Prices are list prices captured on the date shown and are provided for comparison only; check each provider's pricing page before making decisions.
