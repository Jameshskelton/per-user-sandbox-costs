# Cost model

`per-user-sandbox-cost-model.xlsx` estimates the monthly cost of giving every user their own isolated
sandbox, using each provider's published list prices (captured November 19, 2026). Every result is a live
formula: change an input and everything recalculates.

## Sheets

| Sheet | What it holds |
|---|---|
| Read Me | Purpose, color legend, and how the month is modeled |
| Inputs | Workload assumptions (yellow cells) and the scenario switch (`B13`) |
| Rates | Every provider's rates, billing basis, idle defaults, state behavior, source, and capture date |
| Model | Cost per user and for the fleet, plus rebuild columns and rank |
| HourlyCheck | One 2 vCPU / 4 GB sandbox for one hour, fully busy and mostly waiting |
| Sensitivity | Cost by CPU utilization and by memory in use |

Blue text is a hardcoded input, black is a formula, and green links to another sheet.

## Default workload

| Assumption | Value |
|---|---|
| Users, one sandbox each | 1,000 |
| Sessions per user per month | 20 |
| Session length | 45 minutes |
| CPU utilization while working | 25% |
| Sandbox size | 2 vCPU, 4 GB |
| Memory in use (average; also DigitalOcean's peak) | 1.5 GB |
| Disk kept between sessions | 10 GB |
| Full rebuild time | 12.7 s (measured; see `../measurement`) |

## Scenarios

Set `Inputs!B13` to switch:

- **1 = provider defaults:** each provider's out-of-the-box idle timer and state behavior.
- **2 = best configuration:** each provider set to keep as much state as it supports (E2B pause, Daytona Linux VM class, Modal memory snapshots, Cloudflare backups, AWS session storage), with a 1-minute idle timer where configurable. These timers are configured, not defaults; Daytona's VM class, for example, auto-pauses after 60 minutes by default.

| Provider | Default ($/user/month) | Best configuration ($/user/month) |
|---|---|---|
| DigitalOcean Harness Runtime | 1.23 | 1.06 |
| Fly.io Sprites | 1.08 | 1.08 |
| Modal Sandboxes | 1.13 | 1.08 |
| AWS AgentCore Runtime | 1.35 | 1.35 |
| Cloudflare Sandbox | 1.58 | 1.41 |
| E2B | 2.91 | 2.69 |
| Daytona | 3.71 | 2.93 |
| Vercel Sandbox | 3.17 | 3.06 |

DigitalOcean's 1-minute idle timer in the best configuration is an assumption; its docs list no minimum.

## Provider-specific modeling choices

- **DigitalOcean Harness Runtime:** current billing per the public pricing page: CPU at a flat 25% of allocated vCPUs (`Rates!W6 = 0.25`), memory on peak use (`Rates!G6 = 2`, peak in `Inputs!B22`). When active CPU billing ships, set `W6` to 0. The model assumes the default 100-session team limit is raised to fit 1,000 users, at no cost.
- **E2B:** includes the $150/month Pro plan, since the free tier caps concurrency at 20 sandboxes.
- **Modal:** modeled with no resource reservation, so it bills on usage. The 5-minute idle window is an assumed developer-set idle timeout (1 minute in the best configuration), not a Modal default: Modal's documented 5-minute default is a maximum lifetime. Idle time bills memory in use and no CPU; the 0.125-core minimum charge (about $0.03 per user per month) is not modeled.
- **Cloudflare:** billed at 6 GiB, the minimum for a custom 2 vCPU instance.
- **AWS AgentCore Runtime:** v2 consumption rates; idle memory billed for 2 minutes per idle period, since AWS reclaims it after 120 seconds.

## Storage convention

Storage a provider keeps both while a sandbox runs and while it's paused (DigitalOcean session storage, Vercel snapshots, Daytona disk) is billed for the full month: the **Rates** sheet carries a running-disk rate (column I, the monthly rate divided by 730) alongside the paused-storage rate (column K). Fly.io's hot and cold storage are billed for the hours each applies. Vercel's snapshot is assumed to be retained between sessions.

## Excluded

Free credits, model inference, network egress, tool calls, per-creation fees, plan allowances, volume discounts,
DigitalOcean Agent Droplets plan discounts, and snapshot or backup storage for Modal, Cloudflare, and AWS.

## Inputs as plain text

- `price-inputs-2026-11-19.csv` / `.json`: every rate, its unit and billing basis, source URL, and capture date.
- `provider-behavior-2026-11-19.csv`: default isolation, idle timer, what survives a pause, and the best configuration for each provider.

## Using it in Google Sheets

Upload the `.xlsx` to Google Drive and open it with Google Sheets; the formulas carry over. Or use the published
view-only copy: [SHEET COPY URL], which opens your own editable copy.
