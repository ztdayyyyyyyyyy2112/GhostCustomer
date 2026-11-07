# Ghost Customer frontend

Next.js 16 and TypeScript dashboard for the STAT3013 project. The current Overview uses **illustrative mock data**, not study findings.

## Setup

```bash
npm ci
```

Copy `.env.example` to `.env.local` (PowerShell: `Copy-Item .env.example .env.local`), then run:

```bash
npm run dev
```

Open <http://localhost:3000>. `/` redirects to `/dashboard`.

## Data mode

- `NEXT_PUBLIC_API_MODE=mock` (default): local sample responses from `src/mocks/data.json`.
- `NEXT_PUBLIC_API_MODE=real`: requests to `${NEXT_PUBLIC_API_URL}/api/*`. The backend must implement `docs/api_contract.md` at the repository root.
- `NEXT_PUBLIC_MOCK_ERROR=1`: simulate an API failure for the dashboard error state.

The shared client is `src/lib/api.ts`; route components should call it instead of embedding sample values. The contract is a draft pending backend/data/AI review. No inferential statistics or model metrics have been produced yet.

## Checks

```bash
npm run lint
npm run build
```
