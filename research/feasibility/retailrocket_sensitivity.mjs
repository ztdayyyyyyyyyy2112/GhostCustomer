import crypto from 'node:crypto';
import fs from 'node:fs';
import readline from 'node:readline';
import path from 'node:path';
import { createReadStream } from 'node:fs';

const source = process.argv[2] ?? 'data/raw/events.csv';
const reportPath = process.argv[3] ?? 'research/feasibility/retailrocket_sensitivity.md';
const labelPath = process.argv[4] ?? 'data/processed/retailrocket_labels_4-2-2.csv';
const expectedRows = 2_756_101;
const configurations = [[4, 2, 2], [4, 3, 2], [6, 2, 4]];
const thresholds = [0.5, 0.6, 0.7];

async function* csvRows(path) {
  const input = readline.createInterface({ input: createReadStream(path), crlfDelay: Infinity });
  let first = true;
  for await (const line of input) {
    if (first) {
      first = false;
      if (line !== 'timestamp,visitorid,event,itemid,transactionid') throw new Error(`Unexpected CSV header: ${line}`);
      continue;
    }
    const fields = line.split(',');
    if (fields.length !== 5) throw new Error(`Malformed CSV row: ${line.slice(0, 120)}`);
    yield fields;
  }
}

function mondayMs(timestamp) {
  const date = new Date(timestamp);
  const midnight = Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());
  return midnight - ((date.getUTCDay() + 6) % 7) * 86_400_000;
}

function n(value) { return value.toLocaleString('en-US'); }
function pct(value, denominator) { return denominator ? `${(100 * value / denominator).toFixed(1)}%` : '0.0%'; }

const rawStat = { rows: 0, maxId: 0, minTs: Infinity, maxTs: -Infinity, visitors: new Set(), events: { view: 0, addtocart: 0, transaction: 0 } };
for await (const row of csvRows(source)) {
  const ts = Number(row[0]), id = Number(row[1]), event = row[2];
  if (!Number.isSafeInteger(ts) || !Number.isSafeInteger(id) || id < 0 || !(event in rawStat.events)) throw new Error(`Invalid timestamp, visitorid or event at row ${rawStat.rows + 2}`);
  rawStat.rows++;
  rawStat.maxId = Math.max(rawStat.maxId, id);
  rawStat.minTs = Math.min(rawStat.minTs, ts);
  rawStat.maxTs = Math.max(rawStat.maxTs, ts);
  rawStat.visitors.add(id);
  rawStat.events[event]++;
}
if (rawStat.rows !== expectedRows) throw new Error(`Expected ${expectedRows} rows, read ${rawStat.rows}`);

const firstWeekMs = mondayMs(rawStat.minTs) + (rawStat.minTs > mondayMs(rawStat.minTs) ? 7 * 86_400_000 : 0);
const lastWeekMs = mondayMs(rawStat.maxTs);
const weeks = Math.floor((lastWeekMs - firstWeekMs) / (7 * 86_400_000));
if (weeks !== 19) throw new Error(`Expected 19 complete weeks, got ${weeks}`);
const cells = (rawStat.maxId + 1) * weeks;
const engagement = new Uint32Array(cells);
const purchases = new Uint32Array(cells);
for await (const row of csvRows(source)) {
  const ts = Number(row[0]), id = Number(row[1]), event = row[2];
  const weekStart = mondayMs(ts);
  const week = Math.floor((weekStart - firstWeekMs) / (7 * 86_400_000));
  if (week < 0 || week >= weeks) continue;
  const offset = id * weeks + week;
  if (event === 'transaction') purchases[offset]++;
  else engagement[offset]++;
}
const activeWeeksPrefix = new Uint8Array(cells);
for (let id = 0; id <= rawStat.maxId; id++) {
  const base = id * weeks;
  let engagementSum = 0, purchaseSum = 0, activeSum = 0;
  for (let w = 0; w < weeks; w++) {
    engagementSum += engagement[base + w];
    purchaseSum += purchases[base + w];
    activeSum += engagement[base + w] + purchases[base + w] > 0 ? 1 : 0;
    engagement[base + w] = engagementSum;
    purchases[base + w] = purchaseSum;
    activeWeeksPrefix[base + w] = activeSum;
  }
}
const digest = crypto.createHash('sha256');
for await (const chunk of createReadStream(source)) digest.update(chunk);
const sha256 = digest.digest('hex');

function windowCounts(id, start, end) {
  const base = id * weeks;
  const previous = start ? start - 1 : -1;
  const eng = engagement[base + end - 1] - (previous < 0 ? 0 : engagement[base + previous]);
  const purchase = purchases[base + end - 1] - (previous < 0 ? 0 : purchases[base + previous]);
  const activeWeeks = activeWeeksPrefix[base + end - 1] - (previous < 0 ? 0 : activeWeeksPrefix[base + previous]);
  return { eng, purchase, total: eng + purchase, activeWeeks };
}

const configsOut = [];
let labelsCsv = 'visitorid,snapshot_date,baseline_weeks,observation_weeks,confirmation_weeks,history_events,history_active_weeks,baseline_events,observation_views_carts,observation_purchases,confirmation_views_carts,confirmation_purchases,views_carts_decline,ghost_50,ghost_60,ghost_70,label_50,label_60,label_70\n';
const labelCounts = Object.fromEntries(thresholds.map(t => [t, { ghost: 0, active: 0, recovered: 0, inactive: 0, unknown: 0, unscorable_active: 0 }]));
const alternativeGhosts = Object.fromEntries(thresholds.map(t => [t, { view_cart: 0, all_events: 0, view_cart_base: 0, all_events_base: 0 }]));
let labelsCount = 0;

for (const [baselineWeeks, observationWeeks, confirmationWeeks] of configurations) {
  const rules = ['history_only', 'observation_any', 'observation_views_or_cart'];
  const rows = [5, 10].flatMap(minHistoryEvents => [2, 3].flatMap(minActiveWeeks => rules.map(activityRule => ({
    minHistoryEvents, minActiveWeeks, activityRule, eligible: 0, unique: 0, repeated: 0, obsZero: 0, futureZero: 0, bothActive: 0, bothEngaged: 0, censored: 0, eligibleGhost50: 0, completeDates: new Set(), visitorCounts: new Uint8Array(rawStat.maxId + 1),
  }))));
  for (let id = 0; id <= rawStat.maxId; id++) for (let t = baselineWeeks + observationWeeks; t <= weeks; t++) {
    const history = windowCounts(id, t - baselineWeeks - observationWeeks, t);
    const baseline = windowCounts(id, t - baselineWeeks - observationWeeks, t - observationWeeks);
    if (!baseline.total) continue;
    const observation = windowCounts(id, t - observationWeeks, t);
    const isCensored = t + confirmationWeeks > weeks;
    const future = isCensored ? null : windowCounts(id, t, t + confirmationWeeks);
    for (const r of rows) {
      if (history.total < r.minHistoryEvents || history.activeWeeks < r.minActiveWeeks) continue;
      if (r.activityRule === 'observation_any' && !observation.total) continue;
      if (r.activityRule === 'observation_views_or_cart' && !observation.eng) continue;
      if (isCensored) { r.censored++; continue; }
      r.eligible++;
      r.visitorCounts[id] = Math.min(2, r.visitorCounts[id] + 1);
      if (!observation.total) r.obsZero++;
      if (!future.total) r.futureZero++;
      if (observation.total && future.total) r.bothActive++;
      if (observation.eng > 0 && future.eng > 0) {
        r.bothEngaged++;
        if (future.eng / confirmationWeeks <= (observation.eng / observationWeeks) * 0.5) r.eligibleGhost50++;
      }
      r.completeDates.add(t);
    }
  }
  for (const r of rows) {
    for (const count of r.visitorCounts) {
      if (count) r.unique++;
      if (count > 1) r.repeated++;
    }
    delete r.visitorCounts;
    r.completeT = r.completeDates.size;
    delete r.completeDates;
  }
  const primaryRows = rows.filter(r => r.minHistoryEvents === 5 && r.minActiveWeeks === 2);
  configsOut.push({ baselineWeeks, observationWeeks, confirmationWeeks, primary: primaryRows, sensitivity: rows });
}

// One reproducible labeled snapshot table for the recommended 4+2+2 audit scenario.
const [baselineWeeks, observationWeeks, confirmationWeeks] = [4, 2, 2];
for (let id = 0; id <= rawStat.maxId; id++) {
  for (let t = baselineWeeks + observationWeeks; t <= weeks; t++) {
    const history = windowCounts(id, t - baselineWeeks - observationWeeks, t);
    if (history.total < 5 || history.activeWeeks < 2) continue;
    const baseline = windowCounts(id, t - baselineWeeks - observationWeeks, t - observationWeeks);
    if (!baseline.total) continue;
    const observation = windowCounts(id, t - observationWeeks, t);
    const censored = t + confirmationWeeks > weeks;
    const future = censored ? { eng: 0, purchase: 0, total: 0 } : windowCounts(id, t, t + confirmationWeeks);
    const decline = observation.eng > 0 && future.eng > 0 ? 1 - (future.eng / confirmationWeeks) / (observation.eng / observationWeeks) : null;
    const statuses = [];
    for (const threshold of thresholds) {
      let label;
      if (censored) label = 'unknown';
      else if (!future.total) label = 'inactive';
      else if (!observation.total) label = 'recovered';
      else if (decline !== null && decline >= threshold) label = 'ghost';
      else label = 'active';
      statuses.push(label);
      labelCounts[threshold][label]++;
      if (label === 'active' && decline === null) labelCounts[threshold].unscorable_active++;
      if (!censored && observation.eng > 0 && future.eng > 0) {
        alternativeGhosts[threshold].view_cart_base++;
        if (decline >= threshold) alternativeGhosts[threshold].view_cart++;
      }
      if (!censored && observation.total > 0 && future.total > 0) {
        alternativeGhosts[threshold].all_events_base++;
        const allDecline = 1 - (future.total / confirmationWeeks) / (observation.total / observationWeeks);
        if (allDecline >= threshold) alternativeGhosts[threshold].all_events++;
      }
    }
    const d = new Date(firstWeekMs + t * 7 * 86_400_000).toISOString().slice(0, 10);
    labelsCsv += [id, d, baselineWeeks, observationWeeks, confirmationWeeks, history.total, history.activeWeeks, baseline.total, observation.eng, observation.purchase, future.eng, future.purchase, decline === null ? '' : decline.toFixed(6), ...thresholds.map(th => decline !== null && decline >= th ? 1 : 0), ...statuses].join(',') + '\n';
    labelsCount++;
  }
}

for (const threshold of thresholds) {
  const c = labelCounts[threshold];
  const sum = c.ghost + c.active + c.recovered + c.inactive + c.unknown;
  if (sum !== labelsCount) throw new Error(`Label partition failed for ${threshold}: ${sum} != ${labelsCount}`);
}
if (!configsOut.length || !labelsCount || !rawStat.visitors.has(257597)) throw new Error('Self-check failed: no output or known source visitor missing');
fs.mkdirSync(path.dirname(path.resolve(reportPath)), { recursive: true });
fs.mkdirSync(path.dirname(path.resolve(labelPath)), { recursive: true });
fs.writeFileSync(labelPath, labelsCsv, 'utf8');

const main = configsOut.find(c => c.baselineWeeks === 4 && c.observationWeeks === 2 && c.confirmationWeeks === 2);
const pick = (rule) => main.primary.find(r => r.activityRule === rule);
const md = [];
md.push('# Retailrocket snapshot and label sensitivity', '', `Generated: ${new Date().toISOString()}`, '', '## Source check', '', `- File: \`${source}\`; ${n(rawStat.rows)} rows; ${n(rawStat.visitors.size)} visitor IDs; SHA-256 \`${sha256}\`.`, `- Event counts: view ${n(rawStat.events.view)} (${pct(rawStat.events.view, rawStat.rows)}), addtocart ${n(rawStat.events.addtocart)} (${pct(rawStat.events.addtocart, rawStat.rows)}), transaction ${n(rawStat.events.transaction)} (${pct(rawStat.events.transaction, rawStat.rows)}).`, `- Date range: ${new Date(rawStat.minTs).toISOString()} to ${new Date(rawStat.maxTs).toISOString()}; ${weeks} complete Monday weeks from ${new Date(firstWeekMs).toISOString().slice(0,10)} through ${new Date(lastWeekMs).toISOString().slice(0,10)} (end exclusive).`, '- Raw duplicate rows are retained, matching the earlier audit; no item properties/category tree are needed for these event-count labels.', '', '## Candidate windows and eligibility sensitivity', '', 'Base cohort: at least 5 or 10 events in baseline+observation, activity in at least 2 or 3 distinct weeks, and at least one baseline event. `observation_any` additionally requires any event during O; `observation_views_or_cart` requires a view/add-to-cart during O. Snapshot and visitor counts below require a fully observed C horizon; right-censored candidates are listed separately and labeled unknown. Counts below are for min 5 events and 2 active weeks unless stated.', '', '| B+O+C (weeks) | Eligibility rule | Complete snapshots | Visitors | Repeat visitors | No O activity | No C activity | Active in O and C (any event) | Active in O and C (view/cart) | Censored candidates | Ghost at 50%* |', '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|');
for (const c of configsOut) for (const r of c.primary) md.push(`| ${c.baselineWeeks}+${c.observationWeeks}+${c.confirmationWeeks} | ${r.activityRule} | ${n(r.eligible)} | ${n(r.unique)} | ${n(r.repeated)} | ${n(r.obsZero)} | ${n(r.futureZero)} | ${n(r.bothActive)} | ${n(r.bothEngaged)} | ${n(r.censored)} | ${n(r.eligibleGhost50)} (${pct(r.eligibleGhost50, r.bothEngaged)}) |`);
md.push('', '*Ghost50 is the view+cart decline candidate among snapshots with nonzero view+cart activity in both O and C, not a verified churn rate. Sensitivity cells use the same threshold across complete C horizons.*', '', '### 4+2+2 history and activity eligibility', '', '| History minimum | Activity weeks | Rule | Eligible snapshots | Distinct visitors | O/C view+cart active | Ghost at 50% | Ghost rate in comparable O/C cohort |');
for (const r of main.sensitivity) md.push(`| ${r.minHistoryEvents} | ${r.minActiveWeeks} | ${r.activityRule} | ${n(r.eligible)} | ${n(r.unique)} | ${n(r.bothEngaged)} | ${n(r.eligibleGhost50)} | ${pct(r.eligibleGhost50, r.bothEngaged)} |`);
md.push('', '## Candidate labels on the 4+2+2 table', '', 'Operational label rule: `Ghost` means view+addtocart events per week in C are at least the selected percentage lower than in O, while C has some view/cart engagement. `Inactive` means no event of any type in C; `Recovered` means O had no events and C has an event; `Active` means C has an event but does not meet the decline rule; `Unknown` means C is not fully observed. Purchase-only future activity stays active and is not called inactive. Three labels are emitted for threshold sensitivity.', '', '| Decline threshold | Ghost | Active | Recovered | Inactive | Unknown | Unscorable active* | Binary Ghost (O/C view+cart active) | Binary Active | All-event alternative Ghost (same cohort) |', '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|');
for (const threshold of thresholds) {
  const c = labelCounts[threshold];
  md.push(`| ${Math.round(threshold * 100)}% | ${n(c.ghost)} (${pct(c.ghost, labelsCount)} overall) | ${n(c.active)} (${pct(c.active, labelsCount)}) | ${n(c.recovered)} (${pct(c.recovered, labelsCount)}) | ${n(c.inactive)} (${pct(c.inactive, labelsCount)}) | ${n(c.unknown)} (${pct(c.unknown, labelsCount)}) | ${n(c.unscorable_active)} | ${n(alternativeGhosts[threshold].view_cart)} (${pct(alternativeGhosts[threshold].view_cart, alternativeGhosts[threshold].view_cart_base)}) | ${n(alternativeGhosts[threshold].view_cart_base - alternativeGhosts[threshold].view_cart)} (${pct(alternativeGhosts[threshold].view_cart_base - alternativeGhosts[threshold].view_cart, alternativeGhosts[threshold].view_cart_base)}) | ${n(alternativeGhosts[threshold].all_events)} (${pct(alternativeGhosts[threshold].all_events, alternativeGhosts[threshold].view_cart_base)}) |`);
}
md.push('', '*Unscorable active = O or C has no view/cart denominator, but future nonzero event activity keeps the visitor out of Ghost/Inactive. Binary Active equals the comparable O/C-engaged cohort minus Ghost; all-event scoring is shown on that same cohort for sensitivity.*', '', '## Recommendation and limitations', '', '- Recommended audit candidate: **B=4, O=2, C=2 weeks; minimum 5 history events across at least 2 distinct weeks; at least one baseline event; require O view/cart activity for the primary Ghost-vs-Active modeling cohort.** Keep recovered, inactive, and censored unknown as separate outcomes outside that binary cohort.', '- Recommended initial threshold: **50%**, as the proposal’s lower-bound scenario; retain 60% and 70% as sensitivity results. A 50% cutoff is more permissive (larger Ghost class) than 60% or 70%. This is a proposed operational rule, not ground truth or team approval.', '- Use view+addtocart as the engagement numerator and purchases as a separate activity signal. Views are the overwhelming majority of raw events; all-event totals largely become a view count and transactions are sparse.', '- A relative O-to-C label necessarily depends on O. For modeling, report that target construction and either exclude the exact O engagement-rate feature from the Ghost-vs-Active model or compare against a future-only target definition; do not claim an independent label.', '- Keep all snapshots for descriptive flow; for inferential/model evaluation, use a visitor-aware temporal split and prevent one visitor appearing across partitions. There are few distinct T dates, so weekly forecasting remains constrained.', '- Snapshot counts are dependent repeated visitor-rows. The event log has no verified person-level customer identity, session ID, impression/exposure, or item/category context in this file. This output does not test the 30-minute session assumption, deduplicate 460 raw rows, estimate model quality, or validate dataset license for redistribution.', '', '## Generated artifacts', '', `- Labels CSV: \`${labelPath}\` (${n(labelsCount)} visitor-snapshot rows; ignored by Git because it is generated data).`, `- Reproduce: \`node research/feasibility/retailrocket_sensitivity.mjs ${source} ${reportPath} ${labelPath}\`.`, '- Input is read directly; exact SHA-256 appears above. Review and approve D-02/D-03 in `docs/decision_log.md` before copying these labels into report/model claims.');
fs.writeFileSync(reportPath, md.join('\n') + '\n', 'utf8');
console.log(`Rows=${rawStat.rows}; visitors=${rawStat.visitors.size}; weeks=${weeks}; labels=${labelsCount}; SHA256=${sha256}`);
console.log(`Primary 4+2+2 (min5/2 weeks): ${JSON.stringify(pick('history_only'))}`);
console.log(`Labels 50%: ${JSON.stringify(labelCounts[0.5])}`);
console.log(`Labels 60%: ${JSON.stringify(labelCounts[0.6])}`);
console.log(`Labels 70%: ${JSON.stringify(labelCounts[0.7])}`);
console.log(`Wrote ${reportPath} and ${labelPath}`);
