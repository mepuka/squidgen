# imgvec

Photo → cut-out subject → plotter-friendly SVG line drawing.

The active experiment is the FAO cephalopod plate renderer in `imgvec/fao.py`.
It builds a stacked SVG from photo-derived layers: silhouette, internal edge
lines, sparse stipple, sucker rings, and eye marks. The output stays
plotter-oriented: black marks on white, no body fills, and SVG polylines/circles
instead of raster effects.

Iteration outputs are tracked in [docs/eval-history.md](docs/eval-history.md).
The public history keeps generated SVG/PNG candidates and judge JSON, but not
raw source photos or preview contact sheets.

## Setup

```bash
uv sync
```

Requires the linedraw checkout at `/Users/pooks/Dev/linedraw` (referenced as a
local path dependency in `pyproject.toml`).

## Usage

```bash
uv run imgvec -i photo.jpg -o sketch.svg
```

Outputs:

- `sketch.svg` — the vector line drawing
- `sketch.cutout.png` — the segmented subject with transparent background
- `sketch.flat.png` — the cut-out flattened on white (what linedraw saw)

For the FAO renderer:

```bash
uv run imgvec -i photo.jpg -o sketch.svg --profile fao_default
uv run python -m imgvec.harness --self-test
uv run python -m imgvec.harness
```

### Flags

| Flag | Default | Notes |
|---|---|---|
| `--no-segment` | off | Skip rembg; vectorize the raw image. |
| `--no-keep-intermediate` | off | Delete cutout / flat PNGs after run. |
| `--hatch-size N` | 16 | Bigger = sparser hatching. |
| `--contour-simplify N` | 2 | Bigger = fewer outline points. |
| `--no-hatch` | off | Disable hatching. |
| `--no-contour` | off | Disable contours. |

## Programmatic use

```python
from pathlib import Path
from imgvec import run

run(Path("photo.jpg"), Path("sketch.svg"))
```
