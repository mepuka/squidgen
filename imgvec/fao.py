"""FAO-style squid plate renderer.

The code in this module intentionally avoids the dense diagonal hatching used
by linedraw. The target style is a scientific plate: clean outer silhouette,
single-weight outline strokes, sparse stipple, restrained internal edges, and
ring-shaped suckers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from PIL import Image

from imgvec.profiles import Profile


Point = tuple[float, float]
LineLayer = tuple[str, list[list[Point]]]


@dataclass
class SvgDrawing:
    width: float
    height: float
    polylines: list[list[Point]]
    dots: list[tuple[float, float, float]]
    rings: list[tuple[float, float, float]]
    filled_circles: list[tuple[float, float, float]]
    line_layers: list[LineLayer] | None = None
    filled_paths: list[str] | None = None

    @property
    def mark_count(self) -> int:
        line_count = sum(len(lines) for _, lines in self.line_layers) if self.line_layers else len(self.polylines)
        return (
            line_count
            + len(self.dots)
            + len(self.rings) * 2
            + len(self.filled_circles)
            + len(self.filled_paths or [])
        )


def render_fao_svg(
    rgba: Image.Image,
    svg_path: Path,
    profile: Profile,
    *,
    source_rgb: Image.Image | None = None,
) -> SvgDrawing:
    """Render an FAO-style SVG strictly derived from the input segmentation.

    Procedural template fallbacks have been removed: every stroke must come
    from the input photo via _prepare_plate. This is the only allowed code
    path. If the segmentation is empty, _prepare_plate raises rather than
    falling back to a template.
    """
    plate = _prepare_plate(rgba, profile, source_rgb=source_rgb)
    mask = plate["mask"]
    rgb = plate["rgb"]
    offset = float(profile.page_pad)
    height, width = mask.shape
    subject_masks = _split_subject_masks(mask)

    outline_lines = [line for subject_mask in subject_masks for line in _silhouette_lines(subject_mask, profile)]
    appendage_lines = _appendage_centerlines(mask, profile)
    detail_lines = _interior_edge_lines(rgb, mask, profile)
    eye_masks = _eye_subject_masks(subject_masks)
    line_layers = [
        ("outline", _sort_polylines(outline_lines)),
        ("appendage-centerlines", _sort_polylines(appendage_lines)),
        ("photo-detail", _sort_polylines(detail_lines)),
    ]
    if profile.draw_centerline:
        line_layers.append(("body-centerline", _body_centerline(mask, profile)))
    if profile.draw_eye:
        line_layers.append(("eye-outline", [line for subject_mask in eye_masks for line in _eye_lines(rgb, subject_mask, profile)]))

    dots = _stipple_dots(rgb, mask, profile)
    rings = _sucker_rings(rgb, mask, profile)
    filled_circles = [pupil for subject_mask in eye_masks for pupil in _eye_pupils(rgb, subject_mask, profile)]

    drawing = SvgDrawing(
        width=float(width + profile.page_pad * 2),
        height=float(height + profile.page_pad * 2),
        polylines=[
            _offset_line(line, offset, offset)
            for _, lines in line_layers
            for line in lines
        ],
        line_layers=[
            (name, [_offset_line(line, offset, offset) for line in lines])
            for name, lines in line_layers
            if lines
        ],
        dots=_sort_circles([(x + offset, y + offset, r) for x, y, r in dots]),
        rings=_sort_circles([(x + offset, y + offset, r) for x, y, r in rings]),
        filled_circles=[(x + offset, y + offset, r) for x, y, r in filled_circles],
    )
    svg_path.write_text(_svg_text(drawing, profile), encoding="utf-8")
    return drawing


def _prepare_plate(
    rgba: Image.Image,
    profile: Profile,
    *,
    source_rgb: Image.Image | None = None,
) -> dict[str, np.ndarray]:
    rgba = rgba.convert("RGBA")
    source = source_rgb.convert("RGB") if source_rgb is not None else flatten_rgba(rgba)
    if source.size != rgba.size:
        source = source.resize(rgba.size, Image.Resampling.LANCZOS)
    alpha = np.array(rgba.getchannel("A"))
    bbox = Image.fromarray(alpha).point(lambda p: 255 if p > 8 else 0).getbbox()
    if bbox is None:
        raise ValueError("segmentation produced an empty alpha mask")
    pad = max(24, int(max(rgba.size) * 0.025))
    left = max(0, bbox[0] - pad)
    top = max(0, bbox[1] - pad)
    right = min(rgba.width, bbox[2] + pad)
    bottom = min(rgba.height, bbox[3] + pad)
    rgba = rgba.crop((left, top, right, bottom))
    source = source.crop((left, top, right, bottom))

    if profile.rotate_degrees == 90:
        rgba = rgba.transpose(Image.Transpose.ROTATE_90)
        source = source.transpose(Image.Transpose.ROTATE_90)
    elif profile.rotate_degrees == -90:
        rgba = rgba.transpose(Image.Transpose.ROTATE_270)
        source = source.transpose(Image.Transpose.ROTATE_270)
    elif profile.rotate_degrees == 180:
        rgba = rgba.transpose(Image.Transpose.ROTATE_180)
        source = source.transpose(Image.Transpose.ROTATE_180)

    scale = profile.height / rgba.height
    width = max(1, int(round(rgba.width * scale)))
    rgba = rgba.resize((width, profile.height), Image.Resampling.LANCZOS)
    source = source.resize((width, profile.height), Image.Resampling.LANCZOS)

    alpha = np.array(rgba.getchannel("A"))
    alpha_mask = (alpha > 18).astype(np.uint8)
    source_array = np.array(source)
    bg_gray = _border_gray(source_array)
    if source_rgb is not None and bg_gray < 90.0:
        mask = _repair_mask_from_photo(source_array, alpha_mask)
        rgb = source_array
    else:
        mask = alpha_mask
        rgb = np.array(flatten_rgba(rgba))
    mask = _keep_large_components(mask, min_area=45)

    rgb[mask == 0] = 255
    return {"rgb": rgb, "mask": mask}


def _border_gray(rgb: np.ndarray) -> float:
    height, width = rgb.shape[:2]
    border = max(3, int(min(height, width) * 0.035))
    samples = np.concatenate(
        [
            rgb[:border, :, :].reshape(-1, 3),
            rgb[-border:, :, :].reshape(-1, 3),
            rgb[:, :border, :].reshape(-1, 3),
            rgb[:, -border:, :].reshape(-1, 3),
        ],
        axis=0,
    )
    return float(np.mean(np.median(samples.astype(np.float32), axis=0)))


def _repair_mask_from_photo(rgb: np.ndarray, alpha_mask: np.ndarray) -> np.ndarray:
    """Recover faint photo subject regions that rembg made low-alpha.

    The alpha mask remains the anchor. Photo-only pixels are kept only if they
    are visually different from the local background and touch the alpha mask
    after a modest dilation, so watermark/background clutter cannot create a
    separate procedural subject.
    """
    height, width = alpha_mask.shape
    border = max(3, int(min(height, width) * 0.035))
    samples = np.concatenate(
        [
            rgb[:border, :, :].reshape(-1, 3),
            rgb[-border:, :, :].reshape(-1, 3),
            rgb[:, :border, :].reshape(-1, 3),
            rgb[:, -border:, :].reshape(-1, 3),
        ],
        axis=0,
    )
    bg = np.median(samples.astype(np.float32), axis=0)
    diff = np.linalg.norm(rgb.astype(np.float32) - bg[None, None, :], axis=2)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    bg_gray = float(np.mean(bg))
    if bg_gray > 150:
        photo_fg = (diff > 17.0) | (hsv[:, :, 1] > 22) | (gray < bg_gray - 18.0)
    else:
        photo_fg = (diff > 18.0) | (gray > bg_gray + 18.0) | (hsv[:, :, 1] > 24)

    photo_fg = cv2.morphologyEx(photo_fg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8), iterations=1)
    if bg_gray < 90:
        photo_fg = cv2.morphologyEx(photo_fg, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), iterations=2)
    else:
        photo_fg = cv2.morphologyEx(photo_fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)

    seed = cv2.dilate(alpha_mask.astype(np.uint8), np.ones((37, 37), np.uint8), iterations=1)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(photo_fg, 8)
    kept = np.zeros_like(photo_fg, dtype=np.uint8)
    for label in range(1, count):
        component = labels == label
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < 12:
            continue
        if np.any(seed[component] > 0):
            kept[component] = 1

    if bg_gray < 90:
        kept = cv2.morphologyEx(kept, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)
    return ((alpha_mask > 0) | (kept > 0)).astype(np.uint8)


def _detail_mask_from_photo(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    height, width = mask.shape
    border = max(3, int(min(height, width) * 0.035))
    samples = np.concatenate(
        [
            rgb[:border, :, :].reshape(-1, 3),
            rgb[-border:, :, :].reshape(-1, 3),
            rgb[:, :border, :].reshape(-1, 3),
            rgb[:, -border:, :].reshape(-1, 3),
        ],
        axis=0,
    )
    bg = np.median(samples.astype(np.float32), axis=0)
    diff = np.linalg.norm(rgb.astype(np.float32) - bg[None, None, :], axis=2)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    bg_gray = float(np.mean(bg))
    if bg_gray > 150:
        soft = (diff > 8.0) | (hsv[:, :, 1] > 12) | (gray < bg_gray - 9.0)
    else:
        soft = (diff > 8.0) | (gray > bg_gray + 9.0) | (hsv[:, :, 1] > 12)

    local = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8)).apply(gray)
    edges = cv2.Canny(local, 20, 72)
    edge_support = cv2.dilate(edges, np.ones((7, 7), np.uint8), iterations=1) > 0
    near = cv2.dilate(mask.astype(np.uint8), np.ones((95, 95), np.uint8), iterations=1) > 0
    detail = ((mask > 0) | ((soft | edge_support) & near)).astype(np.uint8)
    detail = cv2.morphologyEx(detail, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)
    return detail


def flatten_rgba(rgba: Image.Image) -> Image.Image:
    bg = Image.new("RGB", rgba.size, (255, 255, 255))
    bg.paste(rgba, mask=rgba.getchannel("A"))
    return bg


def _keep_large_components(mask: np.ndarray, min_area: int) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    kept = np.zeros_like(mask)
    for label in range(1, count):
        if stats[label, cv2.CC_STAT_AREA] >= min_area:
            kept[labels == label] = 1
    return kept


def _silhouette_lines(mask: np.ndarray, profile: Profile) -> list[list[Point]]:
    contours, _ = cv2.findContours((mask * 255).astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    lines: list[list[Point]] = []
    for contour in sorted(contours, key=cv2.contourArea, reverse=True):
        area = abs(cv2.contourArea(contour))
        length = cv2.arcLength(contour, True)
        if area < 18 or length < 18:
            continue
        epsilon = max(0.45, length * profile.silhouette_epsilon)
        approx = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2).astype(float)
        if len(approx) < 4:
            continue
        smooth = _chaikin_closed([(float(x), float(y)) for x, y in approx], iterations=1)
        smooth.append(smooth[0])
        lines.append(smooth)
    return lines


def _split_subject_masks(mask: np.ndarray) -> list[np.ndarray]:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    subjects: list[np.ndarray] = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < 45:
            continue
        x, y, w, h = [int(v) for v in stats[label, :4]]
        component = (labels[y : y + h, x : x + w] == label).astype(np.uint8)
        split_rows = _projection_split_rows(component, y)
        if not split_rows:
            out = np.zeros_like(mask)
            out[y : y + h, x : x + w] = component
            subjects.append(out)
            continue

        bounds = [y, *split_rows, y + h]
        for top, bottom in zip(bounds, bounds[1:]):
            if bottom - top < max(24, h * 0.12):
                continue
            out = np.zeros_like(mask)
            local_top = max(0, top - y)
            local_bottom = min(h, bottom - y)
            band = component[local_top:local_bottom]
            if int(band.sum()) < max(180, area * 0.10):
                continue
            out[top:bottom, x : x + w] = band
            subjects.append(out)

    return subjects or [mask]


def _projection_split_rows(component: np.ndarray, y_offset: int) -> list[int]:
    h, w = component.shape
    if h < 180 or w < 420:
        return []
    rows = component.sum(axis=1).astype(np.float32)
    if float(rows.max()) < w * 0.38:
        return []
    kernel = max(17, (h // 12) | 1)
    smooth = cv2.GaussianBlur(rows.reshape(-1, 1), (1, kernel), 0).ravel()
    peak = float(smooth.max())
    if peak <= 0:
        return []

    minima: list[tuple[int, float]] = []
    for idx in range(1, h - 1):
        if smooth[idx] < smooth[idx - 1] and smooth[idx] < smooth[idx + 1]:
            ratio = float(smooth[idx] / peak)
            if 0.45 <= ratio <= 0.88:
                minima.append((idx, ratio))
    if not minima:
        return []

    chosen: list[int] = []
    min_gap = max(80, int(h * 0.16))
    for idx, _ratio in sorted(minima, key=lambda item: item[1]):
        if idx < h * 0.16 or idx > h * 0.90:
            continue
        if all(abs(idx - existing) >= min_gap for existing in chosen):
            chosen.append(idx)
    chosen.sort()
    if len(chosen) < 2:
        return []
    return [y_offset + idx for idx in chosen[:3]]


def _eye_subject_masks(subject_masks: list[np.ndarray]) -> list[np.ndarray]:
    if not subject_masks:
        return []
    areas = [int(mask.sum()) for mask in subject_masks]
    largest = max(areas)
    eye_masks: list[np.ndarray] = []
    for mask, area in zip(subject_masks, areas):
        if area < max(160, largest * 0.18):
            continue
        ys, xs = np.nonzero(mask)
        if len(xs) == 0:
            continue
        width = int(xs.max() - xs.min() + 1)
        height = int(ys.max() - ys.min() + 1)
        if min(width, height) < 18:
            continue
        aspect = max(width, height) / max(1, min(width, height))
        dist = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
        if aspect > 5.5 and area < largest * 0.70:
            continue
        if aspect > 12.0 and float(dist.max()) < 18.0:
            continue
        eye_masks.append(mask)
    return eye_masks or [subject_masks[int(np.argmax(areas))]]


def _interior_edge_lines(rgb: np.ndarray, mask: np.ndarray, profile: Profile) -> list[list[Point]]:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 36, 36)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    local = clahe.apply(gray)

    dist = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    interior = ((dist > 2.0) & (mask > 0)).astype(np.uint8)
    if not np.any(interior):
        return []

    grad_x = cv2.Sobel(local, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(local, cv2.CV_32F, 0, 1, ksize=3)
    grad = cv2.magnitude(grad_x, grad_y)
    grad_values = grad[interior > 0]
    high = float(np.quantile(grad_values, 0.86)) if grad_values.size else 80.0
    high = max(72.0, min(170.0, high))
    low = max(28.0, high * 0.42)

    canny = cv2.Canny(local, int(low), int(high))
    xdog = _xdog_edges(local, interior)
    edges = cv2.bitwise_or(canny, xdog)
    edges = (edges * interior).astype(np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8), iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    candidates: list[tuple[float, list[Point]]] = []
    for contour in contours:
        if len(contour) < 10:
            continue
        length = cv2.arcLength(contour, False)
        if length < profile.min_edge_length:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        if w < 4 and h < 4:
            continue
        if max(w, h) / max(1, min(w, h)) > 42 and length < 90:
            continue
        approx = cv2.approxPolyDP(contour, profile.edge_epsilon, False).reshape(-1, 2)
        line = [(float(x), float(y)) for x, y in approx]
        if len(line) >= 2:
            candidates.append((length, line))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [line for _, line in candidates[: profile.max_edge_lines]]


def _appendage_centerlines(mask: np.ndarray, profile: Profile) -> list[list[Point]]:
    if not np.any(mask):
        return []

    dist = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    skeleton = _skeletonize(mask)
    if not np.any(skeleton):
        return []

    paths = _trace_skeleton_paths(skeleton)
    lines: list[tuple[float, list[Point]]] = []
    for path in paths:
        if len(path) < 12:
            continue
        xs = np.array([p[0] for p in path], dtype=np.int32)
        ys = np.array([p[1] for p in path], dtype=np.int32)
        widths = dist[ys, xs]
        length = _path_length(path)
        if length < 42.0:
            continue
        if float(np.median(widths)) > 26.0:
            continue
        if float(np.quantile(widths, 0.85)) > 42.0:
            continue
        approx = cv2.approxPolyDP(np.array(path, dtype=np.float32).reshape(-1, 1, 2), 1.6, False).reshape(-1, 2)
        line = [(float(x), float(y)) for x, y in approx]
        if len(line) >= 2:
            lines.append((length, line))

    lines.sort(key=lambda item: item[0], reverse=True)
    return [line for _, line in lines[:90]]


def _skeletonize(mask: np.ndarray) -> np.ndarray:
    img = (mask > 0).astype(np.uint8) * 255
    skel = np.zeros_like(img)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    for _ in range(512):
        opened = cv2.morphologyEx(img, cv2.MORPH_OPEN, element)
        temp = cv2.subtract(img, opened)
        skel = cv2.bitwise_or(skel, temp)
        img = cv2.erode(img, element)
        if cv2.countNonZero(img) == 0:
            break
    return (skel > 0).astype(np.uint8)


def _trace_skeleton_paths(skeleton: np.ndarray) -> list[list[tuple[int, int]]]:
    ys, xs = np.nonzero(skeleton)
    points = {(int(x), int(y)) for x, y in zip(xs, ys)}
    if not points:
        return []

    def neighbors(point: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = point
        found: list[tuple[int, int]] = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                candidate = (x + dx, y + dy)
                if candidate in points:
                    found.append(candidate)
        return found

    degree = {point: len(neighbors(point)) for point in points}
    starts = [point for point, count in degree.items() if count != 2]
    if not starts:
        starts = [next(iter(points))]

    visited_edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    paths: list[list[tuple[int, int]]] = []

    def edge_key(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
        return (a, b) if a <= b else (b, a)

    for start in starts:
        for first in neighbors(start):
            key = edge_key(start, first)
            if key in visited_edges:
                continue
            path = [start]
            previous = start
            current = first
            visited_edges.add(key)
            for _ in range(4096):
                path.append(current)
                next_points = [point for point in neighbors(current) if point != previous]
                if len(next_points) != 1:
                    break
                next_point = next_points[0]
                key = edge_key(current, next_point)
                if key in visited_edges:
                    break
                visited_edges.add(key)
                previous, current = current, next_point
            paths.append(path)

    return paths


def _path_length(path: list[tuple[int, int]] | list[Point]) -> float:
    if len(path) < 2:
        return 0.0
    total = 0.0
    for a, b in zip(path, path[1:]):
        total += float(np.hypot(b[0] - a[0], b[1] - a[1]))
    return total


def _xdog_edges(gray: np.ndarray, mask: np.ndarray) -> np.ndarray:
    fine = cv2.GaussianBlur(gray, (0, 0), 0.8).astype(np.float32)
    coarse = cv2.GaussianBlur(gray, (0, 0), 1.8).astype(np.float32)
    dog = fine - 0.98 * coarse
    values = dog[mask > 0]
    if values.size == 0:
        return np.zeros_like(gray, dtype=np.uint8)
    threshold = float(np.quantile(values, 0.13))
    dark_lines = ((dog < threshold) & (mask > 0)).astype(np.uint8) * 255
    dark_lines = cv2.morphologyEx(dark_lines, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8), iterations=1)
    return dark_lines


def _stipple_dots(rgb: np.ndarray, mask: np.ndarray, profile: Profile) -> list[tuple[float, float, float]]:
    rng = np.random.default_rng(profile.seed)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    dark = (255.0 - gray) / 255.0
    saturation = hsv[:, :, 1] / 255.0
    spot = np.clip(dark * 0.62 + saturation * 0.38, 0.0, 1.0)
    local = np.clip(spot - cv2.GaussianBlur(spot, (0, 0), 4.0), 0.0, 1.0)
    weight = np.clip(spot * 0.68 + local * 1.85, 0.0, 1.0)
    weight = cv2.GaussianBlur(weight, (0, 0), 0.65)
    weight[mask == 0] = 0.0

    masked = weight[mask > 0]
    if masked.size == 0:
        return []
    floor = float(np.quantile(masked, 0.84))
    floor = max(0.16, min(0.46, floor))

    height, width = mask.shape

    dots: list[tuple[float, float, float, float]] = []
    step = profile.stipple_step
    for y in range(step, height - step, step):
        for x in range(step, width - step, step):
            jx = int(round(x + rng.uniform(-step * 0.42, step * 0.42)))
            jy = int(round(y + rng.uniform(-step * 0.42, step * 0.42)))
            if jx < 0 or jy < 0 or jx >= width or jy >= height or mask[jy, jx] == 0:
                continue
            w = float(weight[jy, jx])
            if w <= floor:
                continue
            threshold = profile.stipple_strength * ((w - floor) / max(0.001, 1.0 - floor)) ** 1.35
            if rng.random() < threshold:
                radius = 0.34 + min(0.92, w * 1.05) + rng.uniform(-0.08, 0.10)
                dots.append((w, float(jx), float(jy), max(0.42, radius)))

    dots.sort(key=lambda item: item[0], reverse=True)
    kept = [(x, y, r) for _, x, y, r in dots[: profile.max_stipple_dots]]
    kept.extend(_large_chromatophore_dots(weight, mask, limit=240))
    return kept


def _large_chromatophore_dots(weight: np.ndarray, mask: np.ndarray, limit: int) -> list[tuple[float, float, float]]:
    threshold = np.quantile(weight[mask > 0], 0.90) if np.any(mask) else 1.0
    blobs = ((weight >= threshold) & (mask > 0)).astype(np.uint8)
    blobs = cv2.morphologyEx(blobs, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8), iterations=1)
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(blobs, 8)
    dots: list[tuple[float, float, float, float]] = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < 3 or area > 70:
            continue
        x, y = centroids[label]
        radius = min(1.95, max(0.65, (area / np.pi) ** 0.5 * 0.48))
        dots.append((area, float(x), float(y), float(radius)))
    dots.sort(reverse=True)
    return [(x, y, r) for _, x, y, r in dots[:limit]]


def _sucker_rings(rgb: np.ndarray, mask: np.ndarray, profile: Profile) -> list[tuple[float, float, float]]:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    saturation = hsv[:, :, 1]
    height, width = mask.shape
    dist = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    narrow_body = (dist < max(8.0, min(22.0, min(height, width) * 0.026))).astype(np.uint8)
    bright = ((gray > 176) & (saturation < 112) & (mask > 0) & (narrow_body > 0)).astype(np.uint8)
    bright = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(bright, 8)
    rings: list[tuple[float, float, float, float]] = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < 5 or area > 360:
            continue
        x, y = centroids[label]
        bw = stats[label, cv2.CC_STAT_WIDTH]
        bh = stats[label, cv2.CC_STAT_HEIGHT]
        if bw <= 0 or bh <= 0:
            continue
        aspect = bw / bh
        if aspect < 0.34 or aspect > 2.9:
            continue
        perimeter = cv2.arcLength(cv2.findContours((labels == label).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0][0], True)
        circularity = (4.0 * np.pi * area) / max(1.0, perimeter * perimeter)
        if circularity < 0.18:
            continue
        radius = min(profile.sucker_max_radius, max(profile.sucker_min_radius, (area / np.pi) ** 0.5 * 1.05))
        score = area * (0.55 + circularity) + max(0.0, 20.0 - float(dist[int(y), int(x)])) * 3.0
        rings.append((score, float(x), float(y), float(radius)))

    rings.sort(key=lambda item: item[0], reverse=True)
    return [(x, y, r) for _, x, y, r in rings[: profile.sucker_max]]


def _body_centerline(mask: np.ndarray, profile: Profile) -> list[list[Point]]:
    height, width = mask.shape
    ys: list[int] = []
    centers: list[float] = []
    widths: list[int] = []
    for y in range(int(height * 0.37), int(height * 0.96), 10):
        xs = np.flatnonzero(mask[y] > 0)
        if len(xs) < 24:
            continue
        ys.append(y)
        centers.append(float((xs[0] + xs[-1]) / 2))
        widths.append(int(xs[-1] - xs[0]))
    if len(ys) < 8:
        return []
    smooth: list[Point] = []
    for idx, y in enumerate(ys):
        if idx < 2 or idx > len(ys) - 3:
            cx = centers[idx]
        else:
            cx = float(np.mean(centers[idx - 2 : idx + 3]))
        smooth.append((cx, float(y)))
    return [smooth]


def _eye_candidates(rgb: np.ndarray, mask: np.ndarray, profile: Profile) -> list[tuple[float, float, float, float]]:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    dist = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    inside = (mask > 0) & (dist > 3.0)
    values = gray[inside]
    if values.size == 0:
        return []

    dark_cutoff = min(86.0, float(np.quantile(values, 0.045)) + 10.0)
    dark = ((gray <= dark_cutoff) & inside).astype(np.uint8)
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)

    count, labels, stats, centroids = cv2.connectedComponentsWithStats(dark, 8)
    candidates: list[tuple[float, float, float, float, float]] = []
    height, width = mask.shape
    subject_ys, subject_xs = np.nonzero(mask)
    if len(subject_xs) == 0:
        return []
    subject_x0 = int(subject_xs.min())
    subject_x1 = int(subject_xs.max())
    subject_y0 = int(subject_ys.min())
    subject_y1 = int(subject_ys.max())
    subject_w = max(1, subject_x1 - subject_x0 + 1)
    subject_h = max(1, subject_y1 - subject_y0 + 1)
    landscape_subject = subject_w / subject_h > 1.45
    min_area = max(8, int(mask.sum() * 0.00002))
    max_area = max(220, int(mask.sum() * 0.006))
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < min_area or area > max_area:
            continue
        x, y = centroids[label]
        bw = int(stats[label, cv2.CC_STAT_WIDTH])
        bh = int(stats[label, cv2.CC_STAT_HEIGHT])
        if bw <= 1 or bh <= 1:
            continue
        aspect = bw / bh
        if aspect < 0.32 or aspect > 3.6:
            continue
        if landscape_subject:
            y_norm = (float(y) - subject_y0) / subject_h
            if y_norm < 0.20 or y_norm > 0.86:
                continue

        region = labels == label
        contours, _ = cv2.findContours(region.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            continue
        perimeter = cv2.arcLength(contours[0], True)
        circularity = (4.0 * np.pi * area) / max(1.0, perimeter * perimeter)
        if circularity < 0.08:
            continue

        x0 = max(0, int(x) - bw * 2)
        x1 = min(width, int(x) + bw * 2 + 1)
        y0 = max(0, int(y) - bh * 2)
        y1 = min(height, int(y) + bh * 2 + 1)
        local = gray[y0:y1, x0:x1]
        local_mask = mask[y0:y1, x0:x1] > 0
        local_mean = float(local[local_mask].mean()) if np.any(local_mask) else 255.0
        darkness = max(0.0, local_mean - float(gray[int(y), int(x)]))
        sat = float(hsv[int(y), int(x), 1])
        radius = max(2.8, min(13.0, (area / np.pi) ** 0.5 * 1.15))
        score = darkness * 2.4 + area * 0.12 + circularity * 32.0 + sat * 0.02
        candidates.append((score, float(x), float(y), float(radius), float(area)))

    candidates.sort(key=lambda item: item[0], reverse=True)
    component_count, component_labels, component_stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    selected_by_component: dict[int, tuple[float, float, float, float]] = {}
    for score, x, y, radius, _area in candidates:
        label = int(component_labels[int(round(y)), int(round(x))])
        if label <= 0:
            continue
        if label not in selected_by_component:
            selected_by_component[label] = (x, y, radius, score)

    selected: list[tuple[float, float, float, float]] = []
    component_order = sorted(
        selected_by_component,
        key=lambda label: int(component_stats[label, cv2.CC_STAT_AREA]) if label < component_count else 0,
        reverse=True,
    )
    for label in component_order:
        selected.append(selected_by_component[label])
        if len(selected) >= 4:
            break
    if selected:
        return selected

    for score, x, y, radius, _area in candidates:
        if any((x - ox) ** 2 + (y - oy) ** 2 < max(28.0, radius * 4.0) ** 2 for ox, oy, _oradius, _score in selected):
            continue
        selected.append((x, y, radius, score))
        if len(selected) >= 6:
            break
    return selected


def _eye_lines(rgb: np.ndarray, mask: np.ndarray, profile: Profile) -> list[list[Point]]:
    eyes = _eye_candidates(rgb, mask, profile)
    lines: list[list[Point]] = []
    for cx, cy, radius, _score in eyes:
        rx = max(8.5, min(30.0, radius * 2.35))
        ry = max(2.9, rx * 0.42)
        top = _arc(cx, cy, rx, ry, np.pi, 0.0, 18)
        bottom = _arc(cx, cy, rx, ry, np.pi, 2 * np.pi, 18)
        lines.append(top)
        lines.append(bottom)
    return lines


def _eye_pupils(rgb: np.ndarray, mask: np.ndarray, profile: Profile) -> list[tuple[float, float, float]]:
    pupils: list[tuple[float, float, float]] = []
    for cx, cy, radius, _score in _eye_candidates(rgb, mask, profile):
        pupils.append((cx, cy, max(2.6, min(8.0, radius * 0.68))))
    return pupils


def _arc(cx: float, cy: float, rx: float, ry: float, start: float, end: float, count: int) -> list[Point]:
    ts = np.linspace(start, end, count)
    return [(float(cx + np.cos(t) * rx), float(cy + np.sin(t) * ry)) for t in ts]


def _chaikin_closed(points: list[Point], iterations: int) -> list[Point]:
    out = points
    for _ in range(iterations):
        next_points: list[Point] = []
        for idx, p0 in enumerate(out):
            p1 = out[(idx + 1) % len(out)]
            q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
            r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])
            next_points.extend([q, r])
        out = next_points
    return out


def _chaikin_open(points: list[Point], iterations: int) -> list[Point]:
    out = points
    for _ in range(iterations):
        if len(out) < 3:
            return out
        next_points: list[Point] = [out[0]]
        for idx in range(len(out) - 1):
            p0 = out[idx]
            p1 = out[idx + 1]
            q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
            r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])
            next_points.extend([q, r])
        next_points.append(out[-1])
        out = next_points
    return out


def _offset_line(line: Iterable[Point], dx: float, dy: float) -> list[Point]:
    return [(x + dx, y + dy) for x, y in line]


def _sort_polylines(lines: list[list[Point]]) -> list[list[Point]]:
    remaining = [line[:] for line in lines if len(line) >= 2]
    sorted_lines: list[list[Point]] = []
    cursor = (0.0, 0.0)
    while remaining:
        best_idx = 0
        best_reverse = False
        best_dist = float("inf")
        for idx, line in enumerate(remaining):
            start_dist = (line[0][0] - cursor[0]) ** 2 + (line[0][1] - cursor[1]) ** 2
            end_dist = (line[-1][0] - cursor[0]) ** 2 + (line[-1][1] - cursor[1]) ** 2
            if start_dist < best_dist:
                best_idx = idx
                best_reverse = False
                best_dist = start_dist
            if end_dist < best_dist:
                best_idx = idx
                best_reverse = True
                best_dist = end_dist
        line = remaining.pop(best_idx)
        if best_reverse:
            line = list(reversed(line))
        sorted_lines.append(line)
        cursor = line[-1]
    return sorted_lines


def _sort_circles(circles: list[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
    remaining = circles[:]
    sorted_circles: list[tuple[float, float, float]] = []
    cursor = (0.0, 0.0)
    while remaining:
        best_idx = min(
            range(len(remaining)),
            key=lambda idx: (remaining[idx][0] - cursor[0]) ** 2 + (remaining[idx][1] - cursor[1]) ** 2,
        )
        circle = remaining.pop(best_idx)
        sorted_circles.append(circle)
        cursor = (circle[0], circle[1])
    return sorted_circles


def _svg_text(drawing: SvgDrawing, profile: Profile) -> str:
    stroke = _fmt(profile.stroke_width)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'viewBox="0 0 {_fmt(drawing.width)} {_fmt(drawing.height)}" '
        f'width="{_fmt(drawing.width)}" height="{_fmt(drawing.height)}">',
        '<rect width="100%" height="100%" fill="white" />',
    ]
    for path in drawing.filled_paths or []:
        parts.append(f'<path d="{path}" fill="black" stroke="none" />')
    line_layers = drawing.line_layers or [("linework", drawing.polylines)]
    for name, lines in line_layers:
        parts.append(
            f'<g id="{name}" stroke="black" stroke-width="{stroke}" '
            'stroke-linecap="round" stroke-linejoin="round" fill="none">'
        )
        for line in lines:
            if len(line) < 2:
                continue
            points = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in line)
            parts.append(f'<polyline points="{points}" />')
        parts.append("</g>")
    parts.append(
        f'<g id="sucker-rings" stroke="black" stroke-width="{stroke}" '
        'stroke-linecap="round" stroke-linejoin="round" fill="none">'
    )
    for x, y, r in drawing.rings:
        parts.append(f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{_fmt(r)}" />')
        parts.append(f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{_fmt(max(0.75, r * 0.48))}" />')
    parts.append("</g>")
    parts.append('<g id="stipple" fill="black" stroke="none">')
    for x, y, r in drawing.dots:
        parts.append(f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{_fmt(r)}" />')
    parts.append("</g>")
    parts.append('<g id="eye-pupils" fill="black" stroke="none">')
    for x, y, r in drawing.filled_circles:
        parts.append(f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{_fmt(r)}" />')
    parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts)


def _fmt(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")
