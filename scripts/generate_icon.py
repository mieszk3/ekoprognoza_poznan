"""Render the integration brand icons (requires Pillow)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "ekoprognoza_poznan" / "brand"
SUPERSAMPLE = 4
BASE = 512

SKY_TOP = (44, 62, 112)
SKY_BOTTOM = (24, 32, 64)
STONE = (233, 216, 196)
STONE_LIGHT = (247, 238, 226)
OPENING = (28, 20, 36)
LOG = (139, 90, 60)
FLAME_OUTER = (255, 122, 37)
FLAME_INNER = (255, 212, 92)
AIR = (142, 201, 255)


def _bezier(p0, p1, p2, p3, steps=64):
    points = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        points.append(
            (
                u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
                u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1],
            )
        )
    return points


def _flame(cx, base, width, height):
    tip = (cx + 0.08 * width, base - height)
    right = (cx + 0.5 * width, base - 0.35 * height)
    left = (cx - 0.5 * width, base - 0.35 * height)
    bottom = (cx, base)
    return (
        _bezier(tip, (cx + 0.12 * width, base - 0.8 * height), (right[0], base - 0.62 * height), right)
        + _bezier(right, (right[0], base - 0.08 * height), (cx + 0.28 * width, base), bottom)
        + _bezier(bottom, (cx - 0.28 * width, base), (left[0], base - 0.08 * height), left)
        + _bezier(left, (left[0], base - 0.6 * height), (cx - 0.02 * width, base - 0.72 * height), tip)
    )


def render(size: int) -> Image.Image:
    s = size * SUPERSAMPLE

    def px(v: float) -> float:
        return v * s

    sky = Image.new("RGBA", (s, s))
    sky_draw = ImageDraw.Draw(sky)
    for y in range(s):
        t = y / (s - 1)
        color = tuple(round(a + (b - a) * t) for a, b in zip(SKY_TOP, SKY_BOTTOM))
        sky_draw.line([(0, y), (s, y)], fill=color + (255,))

    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=px(0.22), fill=255)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    img.paste(sky, (0, 0), mask)

    draw = ImageDraw.Draw(img)
    line = px(0.028)
    for y, x0, x1 in ((0.15, 0.30, 0.62), (0.22, 0.40, 0.72)):
        draw.line([(px(x0), px(y)), (px(x1), px(y))], fill=AIR + (255,), width=round(line))
        for x in (x0, x1):
            draw.ellipse(
                [px(x) - line / 2, px(y) - line / 2, px(x) + line / 2, px(y) + line / 2],
                fill=AIR + (255,),
            )

    draw.rectangle([px(0.22), px(0.37), px(0.78), px(0.80)], fill=STONE + (255,))
    draw.rounded_rectangle(
        [px(0.15), px(0.30), px(0.85), px(0.375)], radius=px(0.02), fill=STONE_LIGHT + (255,)
    )

    r = 0.16
    draw.rectangle([px(0.5 - r), px(0.58), px(0.5 + r), px(0.80)], fill=OPENING + (255,))
    draw.ellipse([px(0.5 - r), px(0.58 - r), px(0.5 + r), px(0.58 + r)], fill=OPENING + (255,))

    draw.polygon([(px(x), px(y)) for x, y in _flame(0.5, 0.775, 0.24, 0.31)], fill=FLAME_OUTER + (255,))
    draw.polygon([(px(x), px(y)) for x, y in _flame(0.5, 0.775, 0.13, 0.17)], fill=FLAME_INNER + (255,))
    draw.rounded_rectangle([px(0.37), px(0.765), px(0.63), px(0.80)], radius=px(0.015), fill=LOG + (255,))

    draw.rounded_rectangle(
        [px(0.12), px(0.80), px(0.88), px(0.86)], radius=px(0.015), fill=STONE_LIGHT + (255,)
    )

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    render(BASE // 2).save(OUT_DIR / "icon.png", optimize=True)
    render(BASE).save(OUT_DIR / "icon@2x.png", optimize=True)


if __name__ == "__main__":
    main()
