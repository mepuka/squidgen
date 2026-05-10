# Squidgen Iteration Report

Public repo: https://github.com/mepuka/squidgen

## Current Status

The renderer is not at the requested quality gate yet. The last run hit the
planned bail-out condition: several distinct algorithmic changes stayed below
the target range, so this report freezes the current evidence instead of
continuing with low-confidence tweaks.

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
- Recorded additional failed passes for external-only outlines, connected shadow stipple, split cut-edge removal, and centerline-thinned interior detail.

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
- Recent outline and edge-cleanup passes showed the tradeoff clearly: cleaner lines improved some linework scores, but the judge penalized the loss of source-specific anatomy.

## Recent Iterations

- Iteration 18: external-only silhouette contours. Silhouette held, but style regressed.
- Iteration 19: connected shadow-field stipple. Added clutter to the stock fixture.
- Iteration 20: split cut-edge removal. Removed visible artificial lines in a probe, but broke closed-outline scoring.
- Iteration 21: centerline-thinned interior detail. Improved average linework, but lost anatomy and silhouette fidelity.

None of these changes beat iteration 14, so their settings were not kept.

## Next Practical Direction

Small threshold changes are no longer moving the result. The next useful step is
a stronger subject/part separation pass before more style work: recover heads,
arm crowns, tentacles, and individual subjects from the photo/mask, then apply
outline, detail, sucker rings, and stipple to those parts. Without that, the
renderer keeps oscillating between noisy photo tracing and overly generic clean
shapes.

## Verification

Latest kept renderer was verified with:

- `uv run python -m imgvec.harness --self-test`
- full judged harness runs through iteration 21

Iteration 14 remains the best clean scored checkpoint. Iterations 15 through 21
were saved as experiments and their settings were not kept when they regressed.
