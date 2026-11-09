# Ghost Customer frontend

Next.js 16 and TypeScript dashboard for the STAT3013 project. The current Overview uses **illustrative mock data**, not study findings.

The interface uses self-hosted Roboto with Latin and Vietnamese glyphs through `next/font/google`.

## Setup

```bash
npm ci
```

Copy `.env.example` to `.env.local` (PowerShell: `Copy-Item .env.example .env.local`), then run:

```bash
npm run dev
```

Open <http://localhost:3000>. `/` redirects to `/dashboard`.

| Route | Purpose |
| --- | --- |
| `/dashboard` | Overview and dataset notice |
| `/customers` | Search, status filter, sort, and pagination through URL query parameters |
| `/customers/{id}` | Pre-snapshot features and a separate retrospective confirmation timeline |
| `/statistics` | Group distributions, estimates, and test results when available |
| `/forecast` | Observed, fitted, and predicted time series when available |
| `/predict` | Prediction form, model version, score, and available factors |
| `/models` | Held-out metrics and calibration when available |

## Data mode

- `NEXT_PUBLIC_API_MODE=mock` (default): local sample responses from `src/mocks/data.json`.
- `NEXT_PUBLIC_API_MODE=real`: requests to `${NEXT_PUBLIC_API_URL}/api/*`. The backend must implement `docs/api_contract.md` at the repository root.
- `NEXT_PUBLIC_MOCK_ERROR=1`: simulate an API failure to check error states.

The shared client is `src/lib/api.ts`; route components call it instead of embedding sample values. In mock mode, C001 returns an **illustrative** prediction and C005 reports insufficient data. Statistics, forecast, and model metrics show empty states until reproducible results exist. The API contract is a draft pending backend, data, and AI review. See the repository root's `docs/runbook.md` for the real-backend switch and integration checks.

## Checks

```bash
npm run lint
npm run build
```
