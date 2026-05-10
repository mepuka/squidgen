# imgvec FAO-ize — Codex `/goal` Design

Date: 2026-05-09
Status: ready for Codex `/goal` hand-off

## What this document is for

A self-driving Codex `/goal` session that uses the FAO-style squid plate as
an evaluation bench while the *real* purpose is **studying how to turn a
photograph into plotter-ready sorted polylines**. The codex run iterates
across distinct algorithmic moves — different edge detectors, different
shading techniques, different tonality models — and the harness measures
which ones produce drawings that read as FAO-style scientific plates of the
specific input photo.

The output constraint that grounds everything: **sorted polylines a pen
plotter can draw, single-weight, no fills.** Every algorithmic move has to
end at that representation.

The eval gate: across the fixture set in `data/fixtures/`, mean
`style_fidelity ≥ 8/10` and per-fixture min `≥ 7`, sustained 5 consecutive
iterations, judged by Claude with the input photo + the candidate render +
the FAO style references all in scope.

Codex starts here, executes the goal prompt below verbatim, iterates against
the test harness, and stops when the stopping condition is met.

The prior squidgen direction is abandoned. The committed prior design at
`docs/plans/2026-05-09-squidgen-design.md` is historical only and does not
constrain this work.

---

## 1. The goal prompt (paste verbatim into Codex `/goal` — under 4000 chars)

```
/goal Tune imgvec at /Users/pooks/Dev/squidgen until every fixture under data/fixtures/ renders as an SVG line drawing scoring mean style_fidelity ≥ 8/10 across the fixture set, with no single fixture below 7, sustained over 5 consecutive harness iterations, judged by Claude with both the input photo AND the FAO style references in /Users/pooks/Dev/fishdraw/squid_reference_images/*.png in scope.

PRIMARY OBJECTIVE: a vector line drawing that DEPICTS THE INPUT PHOTO in the style of FAO Cephalopods of the World plates. Strokes must be derived from the input — silhouette from the rembg mask edge, internal lines from photo edges, stipple density from photo luminance. FAO style: single-weight black ink polylines on white, sparse stipple confined to shadow envelopes, almond eye + filled pupil, ring-shaped suckers, continuous silhouette, NO solid fills, NO oversized cartoon eyes, NO uniform crosshatch slabs.

HARD BAN — NO PROCEDURAL FALLBACKS. Every stroke, dot, or ring in the output must originate from imgvec.fao._prepare_plate(rgba, profile) and the photo-derived helpers. Do NOT introduce hand-coded mantle/head/fin/arm Bezier templates, do NOT trace a static reference image, do NOT add a "mode" branch that bypasses the photo. The judge now scores silhouette_match 1-10; a hardcoded squid scores ≤ 2 silhouette_match and ≤ 2 style_fidelity. The judge sees the input photo, the candidate render, AND the FAO references — overfitting to the reference style without matching the input is the failure mode this goal exists to prevent.

READ FIRST (in order):
  1. /Users/pooks/Dev/squidgen/docs/plans/2026-05-09-imgvec-faoize-design.md — full spec.
  2. /Users/pooks/Dev/squidgen/imgvec/fao.py — the photo path you are tuning.
  3. /Users/pooks/Dev/squidgen/imgvec/judge.py — the Claude judge prompt (silhouette_match gate is in here).
  4. /Users/pooks/Dev/squidgen/imgvec/harness.py — the eval loop.
  5. /Users/pooks/Dev/linedraw/linedraw.py + filters.py — pattern reference for edge / hatch / stroke-sort. Read-only.

SCOPE: linedraw and fishdraw are FROZEN — read only. imgvec at /Users/pooks/Dev/squidgen is the only repo you write to. Add new modules (e.g. imgvec/passes/<name>.py) freely.

RUNTIME: Python 3.11+ via uv. `uv sync`, `uv add <pkg>`. No JS, no Bun. Judge runs `claude --print` as a subprocess.

LOOP:
  while not done:
    edit imgvec/ algorithm (photo path only)
    uv run python -m imgvec.harness    # one iteration = run + judge over every fixture
    inspect out/eval/<iter>/<fixture>.preview.png  (input | render | refs side-by-side)
    decide next change

PROGRESS.md per iteration line is auto-appended by the harness: timestamp, iteration, profile, fixtures judged, style_fidelity_{mean,min}, silhouette_match_{mean,min}, last5_iter_mean, judge_errors.

DEFINITION OF DONE:
  - uv run python -m imgvec.harness --self-test passes
  - For 5 consecutive iterations: aggregates.style_fidelity_mean ≥ 8.0 AND aggregates.style_fidelity_min ≥ 7 AND aggregates.silhouette_match_min ≥ 6
  - REPORT.md emitted per §9

BAIL-OUTS:
  - Same tweak fails to raise mean score 3× → revert + try a different §4 move
  - Wall-clock 8h → stop, emit REPORT.md
  - Claude judge returns malformed JSON 3× in a row → halt; record in REPORT
  - Mean style_fidelity stuck below 4 across 5 distinct ladder rungs → halt and report

When stopping, emit REPORT.md per §9.
```

---

## 2. References Codex reads

All paths absolute or relative to the squidgen repo root.

| File | Purpose |
|---|---|
| `docs/plans/2026-05-09-imgvec-faoize-design.md` (this file) | Architecture, algorithmic moves, harness spec, stopping conditions. |
| `imgvec/cli.py` | Existing rembg → linedraw → SVG pipeline. The thing you tune. |
| `imgvec/__init__.py` | Re-exports `run`, `segment`, `vectorize`. |
| `pyproject.toml` | uv project; deps via `uv add`. |
| `~/Downloads/Loligo_vulgaris.jpg` | The single training fixture. |
| `/Users/pooks/Dev/linedraw/linedraw.py` | Reference algorithm: edge detection, contour tracing, hatching, stroke sort. Read-only. |
| `/Users/pooks/Dev/linedraw/filters.py` | Sobel/blur/edge masks Codex can copy. |
| `/Users/pooks/Dev/linedraw/strokesort.py` | Pen-travel optimizer Codex can use. |
| `/Users/pooks/Dev/fishdraw/squid_reference_images/*.png` | 6 FAO plates — the style targets passed to the multimodal judge. |
| `/Users/pooks/Dev/fishdraw/test/judge.js` | Pattern reference for how to call Claude as a judge. New judge is Python. |
| `/Users/pooks/Dev/fishdraw/i1920e.pdf` | FAO Cephalopods Vol. 2. Pull more reference plates only if §7's ladder calls for it. |

---

## 3. Architecture

```
photo (jpg/png)
   │
   ▼
┌──────────────────────────┐
│  segmentation (rembg)    │  isolate subject; alpha mask
└──────────┬───────────────┘
           │ RGBA + binary mask
           ▼
┌──────────────────────────┐
│  preprocessing           │  bilateral filter, autocontrast,
│  (imgvec/preprocess.py)  │  optional gamma, sharpen
└──────────┬───────────────┘
           │ enhanced grayscale + mask
           ▼
┌──────────────────────────────────────────────────────┐
│  multi-pass linework (imgvec/passes/*.py)            │
│  • silhouette pass    — clean outer outline          │
│  • detail pass        — XDoG / Canny + thinning      │
│  • shadow envelopes   — multi-tone mask regions      │
│  • stipple pass       — LBG / weighted Voronoi dots  │
│  • hatch pass         — gradient-aligned, multi-tone │
└──────────┬───────────────────────────────────────────┘
           │ list[polyline] + list[dot]
           ▼
┌──────────────────────────┐
│  composite + post        │  vpype-equivalent: linemerge,
│  (imgvec/composite.py)   │  linesimplify, linesort
└──────────┬───────────────┘
           │ ordered polylines
           ▼
┌──────────────────────────┐
│  SVG emit (with viewBox) │
└──────────┬───────────────┘
           │
           ▼
   plotter SVG + intermediate PNGs
```

Codex is free to keep, replace, or reorder any of these passes. The name of
the game is: which combination scores best with the judge.

---

## 4. Algorithmic moves to study

A menu of techniques organised by what they're producing. Codex picks moves
freely; the harness measures which combinations score. Each non-trivial move
should land as `imgvec/passes/<name>.py` so it's swappable and the eval log
can attribute score deltas to specific changes.

### Linework — edges and contours
- Canny on grayscale (current via linedraw)
- **XDoG** (Winnemöller 2012, [paper](https://users.cs.northwestern.edu/~sco590/winnemoeller-cag2012.pdf)) — extended Difference of Gaussians; cleaner ink-style strokes
- **Coherent line drawing** (Kang et al. 2007) — flow-aligned edges that follow form
- **Suggestive Contours** (DeCarlo et al. 2003) — silhouette + view-dependent crease anticipation, the canonical "FAO-shape" technique if you ever lift to a 3D representation
- Sobel + non-max suppression + skeleton thinning + RDP simplify
- Structured Edge Forests (Dollár & Zitnick 2013) — `cv2.ximgproc.createStructuredEdgeDetection`
- Bilateral pre-filter to flatten texture before edges; anisotropic diffusion as a stronger prior

### Contour extraction (mask edge → polyline)
- `cv2.findContours` on the segmentation mask — current path
- Marching squares + RDP for sub-pixel accuracy
- Chaikin / B-spline smoothing — current path uses Chaikin

### Cross-hatching and tone
- Diagonal cross at one threshold (linedraw default — too uniform for FAO)
- **Multi-tone bands**: quantise luminance into 3-4 levels, each gets its own hatch density and direction
- **Gradient-aligned hatch**: hatch direction perpendicular to local image gradient — looks organic, follows form
- **Curvature-aligned hatch**: along estimated principal curvature of an inferred surface
- **Difference-of-Gaussians shading**: use DoG response magnitude to drive hatch density, not raw luminance
- Confine all hatch INSIDE the silhouette mask; never bleed outside

### Stippling and tone-by-density
- Otsu + connected components → blob centers (linedraw / fishdraw style — current)
- **Weighted Voronoi stippling** (Secord 2002)
- **Linde-Buzo-Gray stippling** (Deussen et al. 2017, [paper](https://graphics.uni-konstanz.de/publikationen/Deussen2017LindeBuzoGray/)) — better blue-noise
- Density driven by `(1 - luminance) × saturation` — luminance alone misses chromatophores
- Per-tone-band: lightest band uses stipple, mid uses sparse hatch, dark uses dense hatch

### Value, depth, and form cues
- Shadow envelopes — paint regions of the mask, restrict heavy hatch / stipple to them
- Mantle midline / centerline as a single thin axial stroke (already in `_body_centerline`)
- Optional: lift the mask to a coarse depth map (`cv2.distanceTransform` from silhouette + a Gaussian) and use it to bias hatch density toward the "thicker" part of the body
- Optional: SAM2 part segmentation per arm/fin region, then per-region styling
- Optional: monocular depth estimation (`MiDaS` ONNX) — read depth from the photo; only attempt if cross-hatch tone alone plateaus

### Plotter post-processing — the output constraint
- The output type is `list[list[tuple[float,float]]]` — one polyline per stroke, drawn in order, no overlapping fills
- `uv add vpype-cli` and pipe through `linemerge linesimplify linesort reloop` — or implement equivalents in pure Python under `imgvec/plotter.py`
- Drop polylines shorter than N pixels (noise)
- Pen-travel optimization is what makes a plot good — measure total pen-up distance as a secondary metric

### Style controls (profile knobs)
- `silhouette_weight` — emphasize the outer outline (multi-pass? thicker stroke?)
- `detail_threshold` — interior-edge aggressiveness
- `tone_bands` — 1, 2, or 3 shadow levels
- `hatch_spacing` per band
- `stipple_density` per band
- `seed` — deterministic jitter for sketchy texture

`imgvec/profiles.py` holds named presets. The harness picks the active
profile from CLI flag or env var.

---

## 5. Test harness — `imgvec/harness.py`

Pure Python. Single command: `uv run python -m imgvec.harness`.

### What it does

1. Resolve the fixture: `~/Downloads/Loligo_vulgaris.jpg`. If missing, exit 2.
2. Resolve references: `/Users/pooks/Dev/fishdraw/squid_reference_images/*.png`.
3. Run `imgvec.run(...)` with the active profile → SVG.
4. Render SVG to PNG via `rsvg-convert -w 800 -b white` subprocess.
5. Build the judge prompt; spawn `claude --print --add-dir <root>` with the
   rendered PNG path and reference PNG paths inlined.
6. Parse the JSON the judge returns. Required keys: `linework` (1-10),
   `anatomy` (1-10), `style_fidelity` (1-10), `notes` (string),
   `specific_issues` (list[string]).
7. Append one tight paragraph to `PROGRESS.md`:

   ```
   <ISO timestamp> profile=<name> linework=<int> anatomy=<int> style_fidelity=<int> last5_mean=<float> notes="<short>"
   ```

8. Write `out/eval/<ISO>/loligo.{svg,png,preview.png,judge.json}` for review.
9. Maintain `out/eval/scores.jsonl` — one line per run, full JSON record.
10. `--self-test` mode: skip the Claude call; verify rsvg-convert + imgvec
    round-trip work; assert deterministic output for a fixed seed.

### Why Python (not Bun)

Mirrors fishdraw's harness pattern but stays inside imgvec's uv project so
algorithm tweaks and harness share types and imports.

### Claude judge contract

```json
{
  "linework": 7,
  "anatomy": 8,
  "style_fidelity": 7,
  "notes": "Silhouette is clean. Mantle hatch is too uniform.",
  "specific_issues": ["uniform crosshatch", "missing eye detail"]
}
```

Subprocess invocation (Python):

```python
proc = subprocess.run(
    ["claude", "--print", "--allowedTools", "Read",
     "--add-dir", str(ROOT), "--", PROMPT],
    capture_output=True, text=True, timeout=180,
)
```

Prompt template lives in `imgvec/judge.py`.

If the judge errors 3× in a row → halt; tag in REPORT.

---

## 6. Stopping conditions

```
done = harness_self_test_passes
       AND  mean(style_fidelity for last 5 runs) ≥ 8.0
       AND  min(style_fidelity for last 5 runs)  ≥ 7
```

The 5-run window is restarted from zero whenever any single run drops below
7. This forces a stable mean, not a one-off lucky score.

---

## 7. Iteration ladder

The point of the run is to *try things*, so each rung is a distinct
algorithmic move with its own `imgvec/passes/<name>.py`. Codex reorders
based on judge feedback in `notes` and `specific_issues`. The harness logs
which rungs are active per iteration so we can attribute score deltas.

1. **Multi-tone hatching.** Quantise luminance into 3 bands, give each band
   its own hatch density. Drop the binary cross.
2. **XDoG edges.** Replace Canny with XDoG; tune `sigma`, `k`, `phi`.
3. **Mask-derived silhouette pass.** Separate, single-line outline traced
   from the rembg alpha edge, RDP-simplified, Chaikin-smoothed.
4. **Gradient-aligned hatch.** Hatch direction perpendicular to local image
   gradient. Compare against the diagonal-cross baseline visually and by
   judge score.
5. **Stippling for light band.** LBG or weighted-Voronoi dots in the lightest
   tone band; remove hatch from that band entirely.
6. **Plotter post-processing.** vpype-equivalent line merge / simplify /
   sort. Measure total pen-up travel as a secondary metric.
7. **Perlin jitter.** Small per-vertex displacement on long polylines for a
   hand-drawn feel without breaking the silhouette.
8. **Coherent / suggestive contours.** Flow-aligned edges (Kang) for
   curvilinear features. Optional only if rungs 1-7 plateau.
9. **Depth-biased hatch (optional).** Distance-transform-derived "thickness"
   map as a hatch-density bias. Optional only if 1-8 plateau.
10. **Per-region styling (optional).** SAM2 part masks → different stroke
    treatment per arm / fin / mantle. Optional only if 1-9 plateau.

Each rung records a checkpoint in `out/eval/scores.jsonl` and PROGRESS.md.

---

## 8. Bail-outs

- Same tweak fails to raise mean score 3× → revert; jump to a different ladder rung.
- Wall-clock 8h → stop, emit REPORT.md.
- `claude --print` returns non-JSON 3× in a row → halt; the judge channel is broken.
- Mean style_fidelity stuck below 4 across 5 consecutive distinct rungs → halt; the architecture probably needs a pass redesign rather than a tweak.

---

## 9. REPORT.md format

```markdown
# imgvec Report

## Status
TUNING_COMPLETE | TUNING_BAILED | TUNING_ABANDONED

## Final scores
- last 5 runs: [s1, s2, s3, s4, s5]
- mean: <float>
- best: <int>

## Algorithm timeline
- rung 1 (multi-tone hatch): mean Δ <float>
- rung 2 (XDoG edges): mean Δ <float>
- ...

## Active profile at end
imgvec/profiles.py::<name>

## Reproduction
- `uv sync`
- `uv run python -m imgvec.harness --profile <name>`
- Bun: n/a
- Python: 3.11.x via uv
- Git SHA at finish: <sha>
- Last self-test result: <pass/fail>

## Bail-outs
- <list of any rungs reverted, judge errors, etc.>
```

---

## 10. Out of scope

- Multi-fixture coverage. Loligo is the only fixture for v1.
- Real-time browser UI. Harness is CLI-only.
- Plotter integration (vpype/axicli pipeline). The output is SVG; physical plotter is a separate concern.
- Anything in `/Users/pooks/Dev/fishdraw` or `/Users/pooks/Dev/linedraw`. Read freely; do not modify.
