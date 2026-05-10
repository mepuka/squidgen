# Squidgen Iteration Report

Public repo: https://github.com/mepuka/squidgen

## Current Status

The renderer is not at the requested quality gate yet.

Best clean checkpoint so far is iteration 14:

- mean style fidelity: 4.00
- minimum style fidelity: 3
- mean silhouette match: 5.33
- minimum silhouette match: 3
- judge errors: 0

The target remains:

- mean style fidelity >= 8
- minimum style fidelity >= 7
- minimum silhouette match >= 6
- sustained for 5 consecutive full harness runs

## What Improved

- Created a public repository and pushed the full visible iteration history.
- Added layered SVG output for outline, appendage centerlines, photo detail, eye outlines, sucker rings, stipple, and pupils.
- Recovered the long tentacles in the dark-background fixture.
- Added source-photo mask repair for dark and pure-white backgrounds.
- Added cleaner profile settings: bolder single-weight strokes, smoother silhouettes, sparser stipple, and sorted line/circle plotting order.
- Added tolerant judge parsing for near-complete JSON responses with a missing final brace.
- Repeatedly tested and recorded failed branches instead of silently overwriting them.

## Best Current Behavior

The first fixture now usually reads as the same squid: mantle, fins, long tentacles, and arm fan are present.

The two-view fixture is recognizable in broad layout, but still reads as noisy edge tracing rather than a clean FAO plate.

The stock/multi-squid fixture remains the floor: it preserves only rough mantle bands and does not recover the full heads, arms, tentacles, and subject count.

## Main Remaining Problems

- The multi-squid fixture needs a better subject separation strategy.
- Arms and tentacles are still not cleanly separated into individual appendages.
- Sucker rings are either too subtle or, when widened, become random mantle rings.
- Stipple is still judged as scattered photo noise instead of controlled chromatophore/shadow fields.
- Eye placement and scale are improved but still inconsistent across views.

## Verification

Latest kept renderer was verified with:

- `uv run python -m imgvec.harness --self-test`
- full judged harness runs through iteration 17

Iteration 14 remains the best clean scored checkpoint. Iterations 15, 16, and 17 were saved as failed experiments and their settings were not kept.
