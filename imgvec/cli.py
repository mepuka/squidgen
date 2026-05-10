"""imgvec — segment a subject out of a photo, vectorize it for a plotter.

Usage:
    uv run imgvec -i path/to/photo.jpg -o path/to/sketch.svg

Pipeline:
    1. rembg removes background, returning RGBA with alpha = subject mask.
    2. The masked subject is composited onto white.
    3. linedraw.sketch() converts the flattened image to polylines + writes SVG.

The intermediate cut-out PNG is also saved next to the SVG for inspection.
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path

from PIL import Image

from imgvec.profiles import get_profile


def segment(input_path: Path) -> Image.Image:
    """Run rembg on the input image. Returns an RGBA PIL.Image with alpha=subject."""
    from rembg import remove

    raw = input_path.read_bytes()
    out = remove(raw)
    return Image.open(io.BytesIO(out)).convert("RGBA")


def flatten_on_white(rgba: Image.Image) -> Image.Image:
    """Composite an RGBA image onto a white background. Returns RGB."""
    bg = Image.new("RGB", rgba.size, (255, 255, 255))
    bg.paste(rgba, mask=rgba.split()[3])
    return bg


def vectorize(
    flat_path: Path,
    svg_path: Path,
    *,
    hatch_size: int = 16,
    contour_simplify: int = 2,
    no_hatch: bool = False,
    no_contour: bool = False,
) -> int:
    """Run linedraw on the cut-out and write an SVG. Returns stroke count."""
    import linedraw

    linedraw.export_path = str(svg_path)
    linedraw.draw_hatch = not no_hatch
    linedraw.draw_contours = not no_contour
    linedraw.hatch_size = hatch_size
    linedraw.contour_simplify = contour_simplify
    lines = linedraw.sketch(str(flat_path))
    _rewrite_with_viewbox(svg_path, lines)
    return len(lines)


def vectorize_fao(
    rgba: Image.Image,
    svg_path: Path,
    *,
    profile_name: str | None = None,
) -> int:
    """Write an FAO-style scientific plate SVG. Returns mark count."""
    from imgvec.fao import render_fao_svg

    profile = get_profile(profile_name)
    drawing = render_fao_svg(rgba, svg_path, profile)
    return drawing.mark_count


def _rewrite_with_viewbox(svg_path: Path, lines: list) -> None:
    """linedraw emits an SVG without width/height/viewBox; add them so renderers
    show the full drawing instead of an arbitrary crop."""
    if not lines:
        return
    xs: list[float] = []
    ys: list[float] = []
    for polyline in lines:
        for px, py in polyline:
            # linedraw scales coords by 0.5 in makesvg
            xs.append(px * 0.5)
            ys.append(py * 0.5)
    if not xs:
        return
    minx, miny = min(xs), min(ys)
    maxx, maxy = max(xs), max(ys)
    pad = 4.0
    vb_x = round(minx - pad, 2)
    vb_y = round(miny - pad, 2)
    vb_w = round((maxx - minx) + pad * 2, 2)
    vb_h = round((maxy - miny) + pad * 2, 2)

    body = svg_path.read_text(encoding="utf-8")
    new_open = (
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'viewBox="{vb_x} {vb_y} {vb_w} {vb_h}" '
        f'width="{vb_w}" height="{vb_h}">'
    )
    body = body.replace(
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">',
        new_open,
        1,
    )
    svg_path.write_text(body, encoding="utf-8")


def run(
    input_path: Path,
    output_path: Path,
    *,
    no_segment: bool = False,
    keep_intermediate: bool = True,
    hatch_size: int = 16,
    contour_simplify: int = 2,
    no_hatch: bool = False,
    no_contour: bool = False,
    profile: str | None = None,
) -> dict:
    """Full pipeline. Returns a small report dict."""
    active_profile = get_profile(profile) if profile else None
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    input_path = input_path.resolve()
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    if no_segment:
        raw = Image.open(input_path)
        rgba = raw.convert("RGBA")
        flat = raw.convert("RGB")
        cutout_path = None
    else:
        rgba = segment(input_path)
        flat = flatten_on_white(rgba)
        cutout_path = output_path.with_suffix(".cutout.png")
        rgba.save(cutout_path)

    flat_path = output_path.with_suffix(".flat.png")
    flat.save(flat_path)

    if active_profile is not None:
        strokes = vectorize_fao(rgba, output_path, profile_name=active_profile.name)
    else:
        strokes = vectorize(
            flat_path,
            output_path,
            hatch_size=hatch_size,
            contour_simplify=contour_simplify,
            no_hatch=no_hatch,
            no_contour=no_contour,
        )

    if not keep_intermediate:
        flat_path.unlink(missing_ok=True)
        if cutout_path is not None:
            cutout_path.unlink(missing_ok=True)

    return {
        "input": str(input_path),
        "output_svg": str(output_path),
        "cutout_png": str(cutout_path) if cutout_path else None,
        "flat_png": str(flat_path) if keep_intermediate else None,
        "strokes": strokes,
        "profile": active_profile.name if active_profile else "linedraw",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="imgvec", description=__doc__.splitlines()[0])
    p.add_argument("-i", "--input", dest="input_path", required=True, type=Path)
    p.add_argument("-o", "--output", dest="output_path", required=True, type=Path)
    p.add_argument("--no-segment", action="store_true", help="Skip rembg; vectorize the raw image.")
    p.add_argument("--no-keep-intermediate", action="store_true", help="Delete cutout/flat PNGs after run.")
    p.add_argument("--hatch-size", type=int, default=16)
    p.add_argument("--contour-simplify", type=int, default=2)
    p.add_argument("--no-hatch", action="store_true")
    p.add_argument("--no-contour", action="store_true")
    p.add_argument("--profile", default=None, help="Named profile from imgvec/profiles.py.")
    args = p.parse_args(argv)

    report = run(
        args.input_path,
        args.output_path,
        no_segment=args.no_segment,
        keep_intermediate=not args.no_keep_intermediate,
        hatch_size=args.hatch_size,
        contour_simplify=args.contour_simplify,
        no_hatch=args.no_hatch,
        no_contour=args.no_contour,
        profile=args.profile,
    )

    for key, value in report.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
