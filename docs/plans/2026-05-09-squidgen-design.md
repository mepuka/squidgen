# squidgen — Codex `/goal` Design

A self-driving build of a learned-primitive squid-plate generator, run by Codex
in `/goal` mode. Output: plotter-friendly SVG line drawings that look like FAO
scientific catalog plates.

## What this document is for

Single hand-off document for a Codex `/goal` session. Codex starts here,
executes the goal prompt below verbatim, iterates against the test harness
through three phases (annotator → train primitives → build renderer), and
stops when the stopping conditions are met. No other context required beyond
the references listed in §2.

The sister project at `/Users/pooks/Dev/fishdraw` contains a working procedural
squid generator (`squiddraw.js`) plus extensive anatomy documentation. That
work is **frozen** — read freely as reference, but squidgen takes a different
architectural approach (statistical shape model + learned primitives) and
shares no code with it.

---

## 1. The goal prompt (paste verbatim into Codex — under 4000 chars)

```
/goal Build squidgen at /Users/pooks/Dev/squidgen — a learned-primitive squid-plate generator emitting plotter-friendly SVG line drawings in the style of FAO Cephalopods of the World scientific plates.

PRIMARY OBJECTIVE: visual fidelity to FAO plate aesthetics — line economy, sparse stipple confined to shadow envelopes, single-weight outlines with one shadow accent, concentric-ring suckers, almond eye + filled pupil, continuous fin-mantle silhouette. Anatomical proportions are a soft floor, not the primary goal.

READ FIRST (in order):
  1. /Users/pooks/Dev/squidgen/docs/plans/2026-05-09-squidgen-design.md
     — full spec: architecture (§3), Phase 0 annotator (§4), Phase 1 training (§5), Phase 2 renderer (§6), test harness (§7), stopping conditions (§8), iteration ladder (§9), bail-outs (§10), coding constraints (§11), REPORT format (§12). Everything below references this doc.
  2. /Users/pooks/Dev/fishdraw/SQUID_ANATOMY_MEASUREMENTS.md — landmark schema, FAO measurement ranges.
  3. /Users/pooks/Dev/fishdraw/docs/research/2026-05-08-fao-technique-catalog.md — T1-T20 FAO techniques; each primitive implements these.
  4. /Users/pooks/Dev/fishdraw/squid_reference_images/*.png and i1920e.pdf — plate dataset; pull more from PDF as needed.

SCOPE: fishdraw is FROZEN. Read freely, copy patterns (rndtri, Perlin, polyline ops); do NOT modify or import. squidgen has its own primitives, learned models, and renderer.

RUNTIME: bun for squidgen.js + test/. python 3.11 for tools/ and tools/train_*.py. At runtime, squidgen.js loads models/*.json — no Python.

PHASES (sequential):

  Phase 0 — Annotator. Build tools/annotate.js (Bun server + browser UI) + Python helpers (SAM 2 CoreML, OpenCV stipple/sucker/eye). Verify with `bun tools/annotate.js --self-test`. Then write "PHASE 0 COMPLETE — awaiting user annotation" to PROGRESS.md and STOP. User runs the tool, annotates ≥20 plates across ≥5 species, edits PROGRESS.md to add "ANNOTATIONS READY: <N> plates" before resuming.

  Phase 1 — Training. Run tools/train_*.py to produce models/asm.json, stipple.json, suckers.json, eyes.json, arm_silhouette.json, hatch_patches.bin. Each script cross-validates per §5.

  Phase 2 — Renderer. Build squidgen.js single-file no-deps. Iterate against the 10-tier harness through the 7-rung ladder (§9) until §8 stopping conditions hold.

LOOP (per phase):
  while not done:
    edit code
    bun test/run.js          # appends one paragraph to PROGRESS.md
    inspect out/*.png        # multimodal self-review
    decide next change

PROGRESS.md per turn: timestamp, phase + sub-task, what changed, tier pass/fail, what's next. One tight paragraph; no narration.

DEFINITION OF DONE (full list §8):
  - tools/annotate.js --self-test passes
  - User signaled ANNOTATIONS READY
  - All models/*.json exist and load
  - test/run.js exits 0: T1 100/100 throws, T2 5/5+20/20 ratios, T3-T9 5/5 fixtures, T10 (claude --print or codex exec) ≥7/10 informational

BAIL-OUTS:
  - Phase 0 component fails self-test 3× → stub, continue, flag.
  - Phase 1 training fails CV 3× → ship simpler model, flag.
  - Phase 2 same rung failing 5× → skip rung, flag.
  - Wall-clock 12h → stop, emit REPORT.md.
  - 100 random renders threw ≥5 → halt; correctness regression.

When stopping, emit REPORT.md per design doc §12.
```

---

## 2. References Codex reads

All paths absolute or relative to the squidgen repo root.

| File | Purpose |
|---|---|
| `docs/plans/2026-05-09-squidgen-design.md` (this file) | Architecture, phase plans, primitive specs, training specs, harness design. |
| `/Users/pooks/Dev/fishdraw/SQUID_ANATOMY_MEASUREMENTS.md` | Anatomical schema, per-species measurement ranges with FAO citations. |
| `/Users/pooks/Dev/fishdraw/docs/research/2026-05-08-fao-technique-catalog.md` | T1-T20 FAO drawing techniques. Spec for the primitive library. |
| `/Users/pooks/Dev/fishdraw/squid_reference_images/*.png` | Initial 6-plate dataset. Annotator's first targets. |
| `/Users/pooks/Dev/fishdraw/i1920e.pdf` | FAO Vol. 2 source. Pull more plates as needed via PDF→image extraction in Phase 0. |
| `/Users/pooks/Dev/fishdraw/squiddraw.js` | Reference for landmarks JSON contract, ratio test conventions, rndtri/choice/Perlin patterns (you can reimplement, NOT import). |
| `/Users/pooks/Dev/fishdraw/test/{run,measure,judge,render}.js` | Reference structure for the test harness. |
| `/Users/pooks/Dev/fishdraw/Loligo_vulgaris.landmarks.json` (and 4 siblings) | Example landmarks JSON shape. squidgen produces same schema. |

---

## 3. Architecture

```
species / measurements
       │
       ▼
┌──────────────────────┐
│  Conditional ASM     │ ◄─ trained on landmarks from FAO plates
│  (Procrustes + PCA)  │    classical, ~50 KB, training in seconds
└──────────┬───────────┘
           │ landmark vector + categorical params
           ▼
┌────────────────────────────────────────────────────┐
│  Library of Learned Primitives                     │
│  (each one trained separately on FAO data)         │
│                                                    │
│  • stipple_field    — spatial GMM / DPP            │
│  • sucker_ring      — PCA on B-spline shapes       │
│  • eye              — PCA on hand-traced eyes      │
│  • arm_silhouette   — PCA on arm contour modes     │
│  • hatching_strokes — non-parametric (Efros-Leung) │
│  • photophore       — per-species mixture model    │
│  • mantle_deform    — per-species silhouette modes │
└──────────┬─────────────────────────────────────────┘
           │ polylines + stroke metadata
           ▼
┌──────────────────────┐
│ Compose / clip /     │ deterministic
│ z-order / SVG emit   │
└──────────┬───────────┘
           │
           ▼
   plotter SVG + landmarks JSON
```

**Why this architecture:**
- ASM produces empirically-correlated anatomical shapes, conditioned on species.
  Sample variance and parameter correlations come from FAO data, not from
  hand-tuned procedural distributions.
- Per-primitive learned models capture the things that make FAO plates *look*
  hand-drawn: stipple distribution, sucker shape variance, eye proportions,
  arm contour modes. Each is small enough to train in seconds on M-series.
- Compose step is deterministic — z-order, clipping, line-economy enforcement.
- Test harness is 9-tier deterministic + 1-tier CLI judge (claude/codex), so
  most of the iteration loop runs fast and reproducibly.

**Apple Silicon stack:**
- Training: Python 3.11 + numpy + scipy + scikit-learn + opencv-python.
  All training fits in a single 1-minute script-set on M-series.
- Annotator helpers: Apple CoreML SAM 2 (`apple/coreml-sam2-large`) for plate
  proposal, opencv for stipple/sucker/eye extraction.
- Runtime: pure JS / Bun. No Python at runtime, no MLX, no MPS.
- Judge (test harness): `claude --print` or `codex exec` via Bun.spawn. No
  local VLM.

---

## 4. Phase 0 — The Annotator

`tools/annotate.js` is a Bun server + browser UI for semi-automated annotation
of FAO plates. The user runs it locally, annotates ~20-30 plates over ~3-4
hours (one-time), then signals Codex to proceed to Phase 1.

### 4.1 File layout

```
tools/
├── annotate.js                # Bun server entry
├── public/
│   ├── index.html
│   ├── annotate.js            # canvas + interaction
│   └── style.css
└── helpers/
    ├── pdf_extract.py         # PDF → page PNGs
    ├── sam2_propose.py        # SAM 2 plate boxes (CoreML)
    ├── cv_stipple.py          # Otsu + connected components → dot centers
    ├── cv_suckers.py          # Hough Circles → ring outlines
    ├── cv_eye.py              # active contour → almond outline
    ├── cv_hatch.py            # patch crop on user box
    └── schemas.py             # JSON schema validation
```

### 4.2 Server routes

```
GET  /                        # serves the HTML UI
GET  /healthz                 # liveness probe; verifies all helpers load
GET  /pages?pdf=<path>        # extracts pages from PDF, returns list of PNGs
POST /propose/plates          # body: {page_png}; returns: {boxes: [...]}
POST /propose/stipple         # body: {plate_png, mask}; returns: {dots: [...]}
POST /propose/suckers         # body: {plate_png, click}; returns: {circles: [...]}
POST /propose/eye             # body: {plate_png, click}; returns: {outline: [...]}
POST /save/plate              # body: {plate_png_b64, species, view}; saves to data/plates/
POST /save/landmarks          # body: {plate, landmarks: {...}}
POST /save/stipple            # body: {plate, dots: [...]}
POST /save/suckers            # body: {plate, suckers: [...]}
POST /save/eye                # body: {plate, eye: [...]}
POST /save/hatch_patch        # body: {plate, region, png_b64}
GET  /qa                      # serves QA grid review page
```

### 4.3 Annotator UI modes

**Mode 1 — Plate extraction.** Iterates PDF pages. For each page: SAM 2
proposes mask boxes; user clicks ✓/✗ on each, edits bbox if needed, types
species name (autocomplete from species list per `SQUID_ANATOMY_MEASUREMENTS.md`),
picks view. Saves `data/plates/<species>__<view>.png`.

**Mode 2 — Landmark click-through.** Loads a plate at 2× zoom. Status bar
shows current landmark name and tiny diagram. User clicks; advances to next
landmark. Press `s` to skip occluded. Output: `data/landmarks/<plate>.json`
(schema matching squiddraw's landmarks JSON, see §3.1 of squiddraw-design.md).

**Mode 3 — Stipple extraction.** Otsu threshold + connected components find
dot-sized blobs (area 1-8 px², circularity > 0.6). Browser shows proposed
dots as yellow markers; user paint-erases false positives, paint-adds missed.
Output: `data/stipple/<plate>.json` — list of `{x, y}` centers + region tag.

**Mode 4 — Sucker extraction.** User clicks center of an arm. Tool runs Hough
Circle Transform on a strip around the click. Detected circles in green;
double-click to accept, single-click to reject. For accepted circles, fit
inner ellipse via second Hough pass. Output: `data/suckers/<plate>.json` —
list of `{outer_ring: [points], inner_ring: [points], arm: int}`.

**Mode 5 — Eye extraction.** User clicks eye center. Active contour init from
a small circle expands to high-contrast edge. 8 control points draggable for
refinement. Output: `data/eyes/<plate>.json`.

**Mode 6 — Hatch patch crop.** User drags rectangle over a shaded region.
Saves crop as PNG to `data/hatch_patches/<plate>__<region>.png`. Tag region
type (mantle_dorsal, fin_shadow, etc.).

**Mode 7 — QA review.** Grid view of all annotations with overlays. Validates
landmark consistency across plates, sucker counts plausibility, etc.

### 4.4 Annotator self-test

`bun tools/annotate.js --self-test`:
1. Spawns server on port 3001.
2. Hits `/healthz` — must return 200.
3. Calls each `/propose/*` route with a test image from
   `fishdraw/squid_reference_images/`. Verifies non-empty response.
4. Verifies all JSON schemas validate.
5. Shuts down server, exits 0 if all pass.

This is what the Phase 0 stopping condition checks.

### 4.5 Phase 0 stopping condition

```
phase0_done = annotate_self_test_passes AND
              user_signaled_annotations_ready  # via PROGRESS.md edit
```

Codex writes "PHASE 0 COMPLETE — awaiting user annotation" to PROGRESS.md and
stops. User runs `bun tools/annotate.js`, annotates 20+ plates, then edits
PROGRESS.md to add "ANNOTATIONS READY: <N> plates" and re-invokes Codex.

---

## 5. Phase 1 — Training the learned primitives

Each primitive has its own training script under `tools/train_*.py`. All
scripts share `tools/helpers/training.py` for Procrustes alignment, PCA, and
cross-validation utilities.

### 5.1 `tools/train_asm.py`

Inputs: `data/landmarks/*.json`.
1. Load all landmark sets, parse into `(N, 30, 2)` array.
2. Procrustes-align all to a common reference frame (mean shape).
3. PCA on aligned landmarks → mean shape + top K=8 eigenvectors.
4. Per-species: compute mean and covariance in the PCA latent.
5. Cross-validate: leave-one-out reconstruction RMSE on held-out plate.
   Fail if median reconstruction RMSE > 5px.
6. Save `models/asm.json`:
   ```json
   {
     "mean_shape": [[x, y], ...],
     "eigenvectors": [[[x, y], ...], ...],
     "eigenvalues": [...],
     "species": {
       "Loligo vulgaris": {
         "mean_latent": [...],
         "cov_latent": [[...], ...]
       }
       // ...
     }
   }
   ```

### 5.2 `tools/train_stipple.py`

Inputs: `data/stipple/*.json` + `data/landmarks/*.json` (for geometric features).
1. For each stipple dot, compute geometric features:
   distance-to-silhouette-edge, axial position along mantle, ventral/dorsal
   side flag, region tag (mantle, fin, head, arm).
2. Per region: fit a spatial Gaussian Mixture Model to the (feature) →
   (density) mapping. K=4 components.
3. Cross-validate: leave-one-plate-out, score by log-likelihood on held-out.
4. Save `models/stipple.json`:
   ```json
   {
     "regions": {
       "mantle": {
         "envelope_mask": "...",  // base64-encoded distance field
         "gmm": {"weights": [...], "means": [...], "covs": [...]}
       }
       // ...
     }
   }
   ```

### 5.3 `tools/train_suckers.py`

Inputs: `data/suckers/*.json`.
1. Resample each ring outline to a fixed N=16 control points.
2. Procrustes-align all suckers to canonical orientation + scale.
3. PCA on flattened (N=16 × 2) coordinates × 2 rings = 64 dims.
4. Keep top K=4 modes (~95% variance).
5. Per-species (or per-family): mean and cov in PCA latent.
6. Save `models/suckers.json`.

### 5.4 `tools/train_eyes.py`

Same recipe as suckers but on eye outlines + pupil center/radius.
Save `models/eyes.json`.

### 5.5 `tools/train_arm_silhouette.py`

Inputs: arm contours extracted from `data/landmarks/*.json` (between
`armN_base` and `armN_tip`) plus the user-traced arm strokes.
PCA on contour modes per arm position (I-IV). Save `models/arm_silhouette.json`.

### 5.6 `tools/build_hatch_library.py`

Inputs: `data/hatch_patches/*.png`.
1. Group patches by region tag.
2. Compute patch features (mean intensity, gradient histogram).
3. Save patches as a binary asset bundle: `models/hatch_patches.bin` +
   `models/hatch_patches.json` (index).
4. No "training" — runtime sampling is non-parametric (Efros-Leung).

### 5.7 Phase 1 stopping condition

```
phase1_done = all(model_file_exists(m) for m in [
                "asm", "stipple", "suckers", "eyes", "arm_silhouette",
                "hatch_patches"
              ])
              AND all(cross_validation_passes(m) for m in models_with_cv)
```

---

## 6. Phase 2 — squidgen.js (the renderer)

Single-file, no-deps, runs under bun.

### 6.1 Top-level structure

```js
// squidgen.js
import { sample_asm } from './lib/asm.js';      // these are inline in
import { compose, emit_svg } from './lib/compose.js'; // single-file, but
import * as P from './lib/primitives.js';        // structured logically
// Or: keep all inline in squidgen.js as one file. Either is fine, decide
// based on whether the file stays under ~5000 LOC.

function squid(seed, opts) {
  const params = sample_asm(seed, opts);   // landmarks + categoricals
  const layers = [
    P.mantle(params),
    P.fin_pair(params),                    // merged into mantle silhouette
    P.head_and_eye(params),
    P.funnel(params),
    P.arms(params),                        // 8 arms, with sucker rows
    P.tentacles(params),                   // 2 tentacles + clubs
    P.beak(params),                        // small dark spot
    P.shadow_envelope_stipple(params),     // ONE envelope per region, learned
    P.mantle_midline(params),              // ONE thin axial line
    P.photophores(params),                 // per-species filled ovals
  ];
  return compose(layers, params);          // z-order + clipping + budget check
}
```

### 6.2 Style module

`lib/style.js` (or inline equivalent):

```js
export const STYLE = {
  line_weight: 0.85,                  // single weight everywhere
  shadow_accent_weight: 1.05,         // 1.2× bump on left-third silhouette
  shadow_accent_side: 'left',
  stipple_density_multiplier: 0.4,    // 0.4 = FAO-sparse default
  hatch_fill_style: 'solid_dense_lines',
  // primitives MUST NOT override these. compose() asserts.
};
```

### 6.3 Primitive specs (stroke budgets)

| Primitive | Budget (polylines) | Style notes (per FAO catalog) |
|---|---|---|
| `mantle` | 1 | Continuous fin-mantle silhouette (T6); single weight (T1) |
| `fin_pair` | 0 | Merged into mantle silhouette (T6) |
| `head_and_eye` | 4 | almond + filled pupil (hatch-fill) + cornea arc + olfactory dot (T5) |
| `funnel` | 2 | tube outline + one short dark arc at lumen (T15) |
| `arms` | 3 per arm × 8 = 24 | left contour + right contour + centerline; sucker rows nested |
| `sucker_row` | 2 per sucker | outer ring + inner ring (T3); teeth ticks if size > threshold |
| `tentacles` | 4 per tentacle × 2 = 8 | + club region |
| `club_suckers` | 2 per sucker | inherits sucker_row but with row-pattern only (T13) |
| `beak` | 1 filled spot | small dark spot at arm crown (T18); hatch-filled |
| `shadow_envelope_stipple` | ~30-60 dots per region | constrained to learned shadow envelope (T2) |
| `mantle_midline` | 1 | ONE thin axial line (T7); no parallel midlines |
| `photophores` | N filled ovals | solid black hatched ovals at species-specific positions (T8) |

### 6.4 Compose / clip / z-order

`lib/compose.js`:
1. Collect all polylines from all primitives.
2. Validate stroke budgets. Throw if any primitive exceeded.
3. Z-order: nearest fin → mantle → near arms (I, IV) → head + eye →
   buccal cone → far arms (II, III) → tentacles → beak → photophores.
   (Same ordering as squiddraw's spec Part 2.)
4. Clip back-arm outlines at front-arm boundaries (T14: stop-line junctions).
5. Apply shadow-accent weight bump on the chosen silhouette flank.
6. Emit SVG.

### 6.5 Landmarks JSON output

Same schema as squiddraw's landmarks JSON (see fishdraw/squiddraw.js output
or §3.1 of `fishdraw/docs/plans/2026-05-08-squiddraw-design.md`). Bridge for
the deterministic test harness.

---

## 7. Test harness — 10-tier deterministic + 1-tier judge

### 7.1 File layout

```
test/
├── run.js                    # entrypoint, runs all tiers
├── tiers/
│   ├── t1_throws.js          # 100 random renders without crashing
│   ├── t2_ratios.js          # ratio gates against FAO ranges
│   ├── t3_landmarks.js       # Procrustes-aligned RMSE vs reference
│   ├── t4_silhouette.js      # IoU vs reference plate silhouette
│   ├── t5_chamfer.js         # Chamfer distance edge maps
│   ├── t6_topology.js        # connected components + holes
│   ├── t7_stroke_stats.js    # K-S test on stroke statistics
│   ├── t8_hu_moments.js      # rotation/scale-invariant shape descriptors
│   ├── t9_stipple.js         # stipple density profile
│   └── t10_judge.js          # claude --print / codex exec subprocess
├── fixtures/
│   ├── Loligo_vulgaris.json
│   ├── Doryteuthis_pealeii.json
│   ├── Illex_argentinus.json
│   ├── Architeuthis_dux.json
│   └── Onychoteuthis_banksii.json
└── reference/
    ├── Loligo_vulgaris.png             # FAO plate
    ├── Loligo_vulgaris.landmarks.json  # hand-annotated reference landmarks
    └── ... (one set per species)
```

### 7.2 Per-tier specs

Tiers 1-2 are direct ports of squiddraw's existing harness. Tiers 3-10 are new.

**T1 — Throws.** 100 random unseeded renders. Pass: 0 throws.

**T2 — Ratios.** Per-fixture and per-random-render: assert each
`computed_ratio` (mw_ml_ratio, fin_length_pct_ml, ...) is inside the FAO
range from `SQUID_ANATOMY_MEASUREMENTS.md` Part 3. Per-fixture overrides
tighter than generic. Pass: 5/5 fixtures + 20/20 randoms.

**T3 — Landmarks.** For each fixture, Procrustes-align rendered landmarks to
reference landmarks. Compute per-keypoint RMSE. Pass threshold: median per
fixture < 8 px (loose, since visual is primary).

**T4 — Silhouette IoU.** Rasterize SVG via `@resvg/resvg-js` at 600×1000.
Threshold via Otsu. Compute IoU vs reference plate's binarized silhouette
(after Procrustes alignment of bounding box). Pass: IoU >= 0.70 per fixture.

**T5 — Chamfer.** OpenCV `distanceTransform` on edge maps. Mean Chamfer
distance threshold per fixture < 4.0.

**T6 — Topology.** OpenCV `findContours` with hierarchy. Count connected
components and holes. Per fixture: counts within `[expected - 2, expected + 2]`
range from reference.

**T7 — Stroke stats.** Compute polyline count, total ink length, length
distribution histogram per fixture. K-S test vs per-species reference
distribution. Pass: p > 0.05 per fixture.

**T8 — Hu moments.** OpenCV `HuMoments` on silhouette. Compute log-difference
per moment vs reference. Pass: all 7 log-differences within `[-1, +1]`.

**T9 — Stipple density profile.** Rasterize SVG, threshold, bin inked-pixel
density radially. Compare to reference plate's density profile. Pass:
profiles within KL divergence threshold.

**T10 — Judge (informational, not gating).** Pass `out/<fixture>.png` and
`reference/<species>.png` to `claude --print` (or `codex exec`) with the
FAO-fidelity rubric. Cache by render-hash. Score >= 7/10 per fixture is
the soft target. Logged in REPORT.md but does not affect exit code. (If
the user wants this as a hard gate, flip it via `JUDGE_GATING=1` env var.)

### 7.3 Reference annotation

The user, during Phase 0, annotates the 5 named species fixtures with
reference landmarks (Mode 2) and reference silhouettes (derived from plate
extraction in Mode 1). These become the ground truth for T3-T8.

### 7.4 run.js orchestration

```js
// test/run.js
import { runT1 } from './tiers/t1_throws.js';
// ...

const fixtures = loadFixtures();
const results = { fixtures: {}, randoms: {}, tiers: {} };

// Render fixtures (sequential, stable output order)
for (const fixture of fixtures) {
  const { svg, landmarks } = await renderFixture(fixture);
  results.fixtures[fixture.seed] = { svg, landmarks };
}

// Render 20 random + 100 throw-test in parallel
await Promise.all([
  ...range(20).map(s => renderRandom(s, results.randoms)),
  ...range(100).map(s => throwTest(s, results)),
]);

// Run all tiers
results.tiers.t1 = await runT1(results);
// ...
results.tiers.t10 = await runT10(results);  // judge

writeProgressLine(results);
process.exit(allTiersPass(results) ? 0 : 1);
```

---

## 8. Stopping conditions (recap, machine-checkable)

```
fixtures_pass = all(
  fixture.t2_ratio_pass AND
  fixture.t3_rmse_ok AND
  fixture.t4_iou >= 0.70 AND
  fixture.t5_chamfer_ok AND
  fixture.t6_topology_ok AND
  fixture.t7_strokes_ok AND
  fixture.t9_stipple_ok
  # t10 informational
)
random_ratio_pass = sum(r.t2_ratio_pass for r in random_20) == 20
no_throws = sum(r.threw for r in random_100) == 0

DONE = phase0_done AND phase1_done AND
       fixtures_pass AND random_ratio_pass AND no_throws
```

`run.js` exits 0 iff `DONE`.

---

## 9. Iteration ladder (Phase 2 only)

| Rung | Goal | Notes |
|---|---|---|
| 1 | Mantle silhouette only (continuous fin-mantle); single weight | T1+T2 should already pass |
| 2 | Add head + eye (almond + filled pupil); add funnel | Verify T6 topology correct |
| 3 | Add arms with sucker rows (concentric rings, no teeth yet) | Verify T7 stroke counts plausible |
| 4 | Add tentacles + clubs | Full skeleton |
| 5 | Add shadow_envelope_stipple from learned model | Verify T9 |
| 6 | Add mantle_midline (single line) + beak + photophores | Polish |
| 7 | Tune for 5 fixtures pass | Target stopping conditions |

Codex declares its current rung in each PROGRESS.md update.

---

## 10. Bail-out rules (recap)

- Phase 0 component fails self-test 3× → stub it, continue, flag in REPORT.
- Phase 1 training script fails CV 3× → ship simpler model, flag.
- Phase 2 same rung failing 5× → skip rung, flag, advance.
- Total wall-clock past 12 h → stop and write REPORT.
- 100 random renders threw ≥ 5 → halt (correctness regression).

---

## 11. Coding constraints

**Runtime entrypoint:** `bun squidgen.js` with zero install. Loads
`models/*.json` at startup. No Python at runtime, no MLX, no MPS.

**Single-file or modular:** start single-file. If `squidgen.js` exceeds ~5000
LOC, split under `lib/` but keep module count ≤ 4.

**No npm dependencies in squidgen.js.** Roll your own:
- Random + Perlin noise (port from fishdraw/squiddraw.js — copy, don't import)
- Procrustes alignment (small JS function, ~30 LOC)
- ASM sampling (matrix ops in pure JS, ~50 LOC)
- B-spline evaluation (~30 LOC)
- Polyline ops (resample, simplify, clip, bbox)

**Test harness allowed deps** (install via `bun add`, commit lockfile):
- `@resvg/resvg-js` — SVG → PNG.
- `opencv-wasm` (or shell out to a Python helper for OpenCV ops).
- Bun built-ins: `Bun.file`, `Bun.write`, `Bun.spawn`, `Bun.hash`.

**Python deps (training + helpers, install via pip, commit requirements.txt):**
- numpy, scipy, scikit-learn, opencv-python, pillow, pdf2image
- coremltools (only if SAM 2 CoreML helper needs runtime conversion)

**Judge subprocess:** `claude --print` or `codex exec`. Cache results by
`Bun.hash(svg_string)` to avoid duplicate calls.

---

## 12. Final REPORT.md (Codex emits when stopping)

Single markdown file, ≤ 400 lines:

1. **Status** — DONE / STUCK / TIMEOUT / REGRESSION / PHASE_0_AWAITING_USER /
   PHASE_1_FAILED / PHASE_2_STUCK
2. **Phase summary** — Phase 0, 1, 2 each with done/skipped/notes.
3. **Stopping condition table** — each line of §8 with `pass | fail | n/a`.
4. **Per-fixture summary** — each species: T1-T10 results, sample render path,
   judge score + notes.
5. **Random eval summary** — pass rate per tier.
6. **Rungs completed** — 1 through 7, with notes per rung.
7. **Models trained** — for each `models/*.json`, file size + cross-validation
   metrics.
8. **Bail-outs** — anything skipped or flagged for human eyes.
9. **Reproduction** — exact `bun test/run.js` invocation, bun version, python
   version, last commit SHA, model file sizes, training durations.

---

## 13. Out of scope (v1)

- Octopus, cuttlefish, nautilus.
- Animated SMIL output.
- Multiple-view rendering (lateral only; ventral/dorsal in v2).
- Display-pattern variation (mottled, transverse_bands). Add as one optional
  knob in v2.
- Active learning loop in the annotator (start over with classical CV; add
  ML refinements in v2 if needed).
- Hectocotylus rendering (males of certain species). v2.
- Full automated PDF figure-caption pairing (Docling integration). v2 — for
  v1, manual plate naming in the annotator is fine.
- Custom ControlNet training. v2 if v1's learned-primitives approach needs
  augmenting.
