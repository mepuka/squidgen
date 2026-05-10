"""Claude judge integration for the FAO style harness."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {"linework", "anatomy", "style_fidelity", "silhouette_match", "notes", "specific_issues"}


@dataclass
class JudgeError(Exception):
    message: str
    stdout: str = ""
    stderr: str = ""

    def __str__(self) -> str:
        return self.message


def judge_with_claude(
    *,
    root: Path,
    input_photo: Path,
    generated_png: Path,
    references: list[Path],
    timeout: int = 240,
) -> dict[str, Any]:
    prompt = build_prompt(
        root=root,
        input_photo=input_photo,
        generated_png=generated_png,
        references=references,
    )
    add_dirs = [root, generated_png.parent, input_photo.parent]
    for ref in references:
        parent = ref.parent
        if parent not in add_dirs:
            add_dirs.append(parent)
    cmd = ["claude", "--print", "--allowedTools", "Read"]
    for directory in add_dirs:
        cmd.extend(["--add-dir", str(directory)])
    cmd.extend(["--", prompt])
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise JudgeError(
            f"Claude judge exited with {proc.returncode}",
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    return parse_judge_json(proc.stdout)


def build_prompt(
    *,
    root: Path,
    input_photo: Path,
    generated_png: Path,
    references: list[Path],
) -> str:
    ref_lines = "\n".join(f"- {ref}" for ref in references)
    return f"""
You are judging whether a generated SVG line drawing faithfully renders a SPECIFIC INPUT PHOTO in the style of FAO Cephalopods of the World reference plates.

Read all three image groups before scoring:

Input photo (the subject the generator was given):
{input_photo}

Generated PNG (the candidate output to score):
{generated_png}

FAO style reference plates (the target visual style only):
{ref_lines}

CRITICAL RULE — silhouette must match the input photo. The generated drawing must depict the SAME individual squid as the input photo, in roughly the same pose, with the same proportions and the same arm/tentacle arrangement. A drawing that looks like an FAO plate but does not match the input silhouette is a failure regardless of style quality. Suspected procedurally-generated or template-traced output (a generic cephalopod that does not match the input pose, arm count visible from the photo, head/mantle ratio, etc.) must score `silhouette_match` ≤ 2 and `style_fidelity` ≤ 2.

Return strict JSON only with exactly these keys:
linework, anatomy, style_fidelity, silhouette_match, notes, specific_issues.

All four numeric keys (linework, anatomy, style_fidelity, silhouette_match) are integers from 1 to 10.

silhouette_match is a hard gate. Score 1-3 = wrong subject / generic shape; 4-6 = roughly the right subject but distorted; 7-8 = recognisably the same squid; 9-10 = unmistakably this exact photo, posed and proportioned faithfully.

style_fidelity scores how closely the generated image reads as an FAO scientific cephalopod plate, but ONLY count it if silhouette_match ≥ 5 — otherwise cap style_fidelity at silhouette_match.

Reward in style_fidelity:
- single-weight black ink linework on white
- clean continuous fin-mantle silhouette tracing the input photo's outline
- sparse stipple concentrated in the same shadow / chromatophore fields visible in the photo
- almond eye with small filled pupil placed where the eye is in the photo
- ring-shaped suckers along arms where visible in the photo
- scientific plate restraint rather than cartoon or photo filter artifacts

Penalize in style_fidelity (and reflect in specific_issues):
- solid filled body regions
- oversized cartoon eyes
- dense uniform crosshatch slabs
- noisy photo-trace clutter
- missing arms, missing tentacles, or extra appendages relative to the input
- broken silhouette
- output that looks like a generic FAO plate rather than this specific photo

`notes` is a one-sentence summary. `specific_issues` is a list of short strings calling out concrete defects.

Return JSON only. No markdown.
""".strip()


def parse_judge_json(stdout: str) -> dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", stdout)
    candidates: list[str] = []
    if match:
        candidates.append(match.group(0))
    else:
        start = stdout.find("{")
        if start >= 0:
            candidate = stdout[start:].strip()
            missing_braces = candidate.count("{") - candidate.count("}")
            if missing_braces > 0:
                candidate = f"{candidate}{'}' * missing_braces}"
            candidates.append(candidate)
    if not candidates:
        raise JudgeError("Claude judge did not return a JSON object", stdout=stdout)

    last_error: json.JSONDecodeError | None = None
    for candidate in candidates:
        try:
            data = json.loads(candidate)
            break
        except json.JSONDecodeError as exc:
            last_error = exc
    else:
        assert last_error is not None
        raise JudgeError(f"Claude judge returned malformed JSON: {last_error}", stdout=stdout) from last_error

    missing = REQUIRED_KEYS.difference(data)
    if missing:
        raise JudgeError(f"Claude judge JSON missing keys: {sorted(missing)}", stdout=stdout)
    for key in ("linework", "anatomy", "style_fidelity", "silhouette_match"):
        value = data[key]
        if not isinstance(value, int) or not 1 <= value <= 10:
            raise JudgeError(f"Claude judge key {key!r} is not an integer 1-10", stdout=stdout)
    if not isinstance(data["notes"], str):
        raise JudgeError("Claude judge key 'notes' is not a string", stdout=stdout)
    if not isinstance(data["specific_issues"], list):
        raise JudgeError("Claude judge key 'specific_issues' is not a list", stdout=stdout)
    return data
