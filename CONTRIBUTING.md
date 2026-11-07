# Contributing

1. Update `develop` and create a short `feature/*` branch for one task.
2. Document the intended input, output, and owner in an issue or PR description.
3. For shared fields, update `docs/api_contract.md` and the matching types/examples in the same PR. Tag the data, backend, frontend, and AI owners for review.
4. Run the relevant setup, lint, build, or tests and record the result in the PR.
5. Open the PR against `develop`; request at least one teammate review before merge. Do not force-push shared branches.

Use mock values only for interface development. Label them as illustrative in the UI and documentation. Statistical results must be generated from a reproducible analysis and include the sample size, method, and assumptions.
