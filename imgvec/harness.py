"""FAO style evaluation harness.

Run:
    uv run python -m imgvec.harness
    uv run python -m imgvec.harness --self-test

One iteration runs imgvec on every fixture in data/fixtures/, judges each
result via Claude (with the input photo + generated PNG + FAO style refs),
aggregates per-iteration stats, appends a one-line PROGRESS.md entry, and
writes per-fixture artefacts under out/eval/<iter>-<timestamp>/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from imgvec import run
from imgvec.judge import JudgeError, judge_with_claude
from imgvec.profiles import get_profile


ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "data" / "fixtures"
REF_DIR = Path("/Users/pooks/Dev/fishdraw/squid_reference_images")
SCORES_PATH = ROOT / "out" / "eval" / "scores.jsonl"
PROGRESS_PATH = ROOT / "PROGRESS.md"

FIXTURE_GLOBS = ("*.jpg", "*.jpeg", "*.png", "*.webp")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the imgvec FAO judge harness.")
    parser.add_argument("--profile", default=os.environ.get("IMGVEC_PROFILE", "fao_default"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    profile = get_profile(args.profile)
    if args.self_test:
        self_test(profile.name)
        print("self-test: pass")
        return 0
    run_harness(profile.name)
    return 0


def list_fixtures() -> list[Path]:
    fixtures: list[Path] = []
    for pattern in FIXTURE_GLOBS:
        fixtures.extend(sorted(FIXTURES_DIR.glob(pattern)))
    if not fixtures:
        raise SystemExit(f"no fixtures found under {FIXTURES_DIR}; add input photos there")
    return fixtures


def run_harness(profile_name: str) -> dict[str, Any]:
    fixtures = list_fixtures()
    references = sorted(REF_DIR.glob("*.png"))
    if not references:
        raise SystemExit(f"missing reference PNGs: {REF_DIR}")

    iteration = _next_iteration_index()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    eval_dir = _next_eval_dir(iteration, timestamp)
    eval_dir.mkdir(parents=True, exist_ok=False)

    per_fixture: list[dict[str, Any]] = []
    judge_errors: list[dict[str, Any]] = []

    for fixture in fixtures:
        stem = fixture.stem
        svg_path = eval_dir / f"{stem}.svg"
        png_path = eval_dir / f"{stem}.png"
        preview_path = eval_dir / f"{stem}.preview.png"
        judge_path = eval_dir / f"{stem}.judge.json"

        report = run(fixture, svg_path, profile=profile_name)
        render_svg(svg_path, png_path, width=800)
        write_preview(fixture, png_path, references, preview_path)

        entry: dict[str, Any] = {
            "fixture": str(fixture),
            "stem": stem,
            "svg": str(svg_path),
            "png": str(png_path),
            "preview": str(preview_path),
            "report": report,
        }
        try:
            judgment = judge_with_claude(
                root=ROOT,
                input_photo=fixture,
                generated_png=png_path,
                references=references,
            )
            entry.update(judgment)
            judge_path.write_text(json.dumps(judgment, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except (JudgeError, subprocess.TimeoutExpired) as exc:
            err = {
                "fixture": str(fixture),
                "error": str(exc),
                "stdout": getattr(exc, "stdout", ""),
                "stderr": getattr(exc, "stderr", ""),
            }
            judge_errors.append(err)
            entry["judge_error"] = err
            judge_path.write_text(json.dumps(err, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        per_fixture.append(entry)

    aggregates = _aggregate(per_fixture)

    record: dict[str, Any] = {
        "iteration": iteration,
        "timestamp": timestamp,
        "profile": profile_name,
        "fixtures": per_fixture,
        "aggregates": aggregates,
        "judge_errors": judge_errors,
        "eval_dir": str(eval_dir),
    }

    _append_score(record)
    _append_progress(record)
    print(json.dumps(_brief(record), indent=2, sort_keys=True))

    if judge_errors and len(judge_errors) == len(fixtures):
        raise SystemExit("every fixture failed to judge; halting")
    return record


def self_test(profile_name: str) -> None:
    fixtures = list_fixtures()
    out_dir = ROOT / "out" / "self-test"
    out_dir.mkdir(parents=True, exist_ok=True)
    fixture = fixtures[0]
    first = out_dir / f"{fixture.stem}.first.svg"
    second = out_dir / f"{fixture.stem}.second.svg"
    png = out_dir / f"{fixture.stem}.png"
    run(fixture, first, profile=profile_name)
    run(fixture, second, profile=profile_name)
    first_hash = hashlib.sha256(first.read_bytes()).hexdigest()
    second_hash = hashlib.sha256(second.read_bytes()).hexdigest()
    if first_hash != second_hash:
        raise AssertionError("fixed profile did not produce deterministic SVG output")
    render_svg(first, png, width=800)
    if not png.exists() or png.stat().st_size <= 0:
        raise AssertionError("rsvg-convert did not produce a PNG")


def render_svg(svg_path: Path, png_path: Path, *, width: int) -> None:
    subprocess.run(
        ["rsvg-convert", "-w", str(width), "-b", "white", str(svg_path), "-o", str(png_path)],
        check=True,
        capture_output=True,
        text=True,
    )


def write_preview(input_photo: Path, candidate_path: Path, references: list[Path], preview_path: Path) -> None:
    """Side-by-side: input photo · generated drawing · 4 FAO style refs."""
    photo = Image.open(input_photo).convert("RGB")
    photo.thumbnail((520, 720), Image.Resampling.LANCZOS)
    candidate = Image.open(candidate_path).convert("RGB")
    candidate.thumbnail((520, 720), Image.Resampling.LANCZOS)
    ref_images: list[Image.Image] = []
    for ref in references[:4]:
        img = Image.open(ref).convert("RGB")
        img = ImageOps.contain(img, (220, 220), Image.Resampling.LANCZOS)
        ref_images.append(img)

    ref_w = 460
    width = photo.width + 12 + candidate.width + ref_w + 48
    height = max(photo.height, candidate.height, 700)
    sheet = Image.new("RGB", (width, height), (255, 255, 255))
    sheet.paste(photo, (18, 18))
    sheet.paste(candidate, (photo.width + 30, 18))
    x0 = photo.width + 12 + candidate.width + 42
    y = 18
    for idx, img in enumerate(ref_images):
        x = x0 + (idx % 2) * 224
        if idx and idx % 2 == 0:
            y += 224
        sheet.paste(img, (x, y))
    sheet.save(preview_path)


def _aggregate(per_fixture: list[dict[str, Any]]) -> dict[str, Any]:
    style = [int(e["style_fidelity"]) for e in per_fixture if isinstance(e.get("style_fidelity"), int)]
    sil = [int(e["silhouette_match"]) for e in per_fixture if isinstance(e.get("silhouette_match"), int)]
    line = [int(e["linework"]) for e in per_fixture if isinstance(e.get("linework"), int)]
    anat = [int(e["anatomy"]) for e in per_fixture if isinstance(e.get("anatomy"), int)]
    return {
        "fixture_count": len(per_fixture),
        "judged_count": len(style),
        "style_fidelity_mean": _mean(style),
        "style_fidelity_min": min(style) if style else None,
        "silhouette_match_mean": _mean(sil),
        "silhouette_match_min": min(sil) if sil else None,
        "linework_mean": _mean(line),
        "anatomy_mean": _mean(anat),
    }


def _mean(values: list[int]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _append_score(record: dict[str, Any]) -> None:
    SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SCORES_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _append_progress(record: dict[str, Any]) -> None:
    iter_means: list[float] = []
    for past in _read_scores()[-5:]:
        m = past.get("aggregates", {}).get("style_fidelity_mean")
        if isinstance(m, (int, float)):
            iter_means.append(float(m))
    last5_mean = round(sum(iter_means) / len(iter_means), 2) if iter_means else None

    agg = record["aggregates"]
    timestamp = record["timestamp"]
    iteration = record["iteration"]
    profile = record["profile"]
    fixtures = agg["fixture_count"]
    judged = agg["judged_count"]
    style_mean = agg["style_fidelity_mean"]
    style_min = agg["style_fidelity_min"]
    sil_mean = agg["silhouette_match_mean"]
    sil_min = agg["silhouette_match_min"]
    judge_errors = len(record.get("judge_errors", []))
    line = (
        f"{timestamp} iteration={iteration} profile={profile} fixtures={fixtures} judged={judged} "
        f"style_mean={style_mean} style_min={style_min} silhouette_mean={sil_mean} silhouette_min={sil_min} "
        f"last5_iter_mean={last5_mean} judge_errors={judge_errors}"
    )
    with PROGRESS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _read_scores() -> list[dict[str, Any]]:
    if not SCORES_PATH.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in SCORES_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(json.loads(line))
    return records


def _next_iteration_index() -> int:
    return len(_read_scores()) + 1


def _brief(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "iteration": record["iteration"],
        "timestamp": record["timestamp"],
        "profile": record["profile"],
        "aggregates": record["aggregates"],
        "judge_errors": len(record.get("judge_errors", [])),
        "eval_dir": record["eval_dir"],
    }


def _next_eval_dir(iteration: int, timestamp: str) -> Path:
    base = ROOT / "out" / "eval" / f"{iteration:04d}-{timestamp}"
    if not base.exists():
        return base
    suffix = 2
    while True:
        candidate = ROOT / "out" / "eval" / f"{iteration:04d}-{timestamp}-{suffix}"
        if not candidate.exists():
            return candidate
        suffix += 1


if __name__ == "__main__":
    raise SystemExit(main())
