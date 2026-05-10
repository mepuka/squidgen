"""Named rendering profiles for imgvec.

All profiles route through the photo-driven path in `imgvec.fao.render_fao_svg`.
Procedural template fallbacks have been removed; the `mode` field is preserved
for backwards compatibility with serialised configs but no longer changes the
code path.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    name: str
    mode: str = "photo"
    seed: int = 17
    rotate_degrees: int = 0
    height: int = 1240
    page_pad: int = 42
    stroke_width: float = 1.12
    silhouette_epsilon: float = 0.0016
    edge_epsilon: float = 1.25
    min_edge_length: float = 28.0
    max_edge_lines: int = 260
    stipple_step: int = 6
    stipple_strength: float = 0.42
    max_stipple_dots: int = 3000
    sucker_max: int = 180
    sucker_min_radius: float = 2.4
    sucker_max_radius: float = 8.2
    draw_eye: bool = True
    draw_centerline: bool = False


PROFILES: dict[str, Profile] = {
    "fao_default": Profile(name="fao_default"),
    "fao_sparse": Profile(
        name="fao_sparse",
        seed=23,
        stipple_step=6,
        stipple_strength=0.34,
        max_stipple_dots=2600,
        max_edge_lines=120,
        sucker_max=100,
    ),
    "fao_dense": Profile(
        name="fao_dense",
        seed=31,
        stipple_step=4,
        stipple_strength=0.52,
        max_stipple_dots=5200,
        max_edge_lines=220,
        sucker_max=160,
    ),
}


def get_profile(name: str | None) -> Profile:
    key = name or "fao_default"
    try:
        return PROFILES[key]
    except KeyError as exc:
        choices = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown profile {key!r}; expected one of: {choices}") from exc
