#!/usr/bin/env python3
"""
dotify.py - turn a photo into dot-matrix / binary-grid art as an SVG with optional clear image embedding and loading animations.
Usage:
    python dotify.py me.jpg -o assets/portrait
    python dotify.py me.jpg -o assets/portrait --mode binary --cols 64
    python dotify.py me.jpg -o assets/portrait --circle --animate --color
    python dotify.py me.jpg -o assets/portrait --cols 100 --color --reveal --embed-image --dots-fade-out
"""
from __future__ import annotations
import argparse
import math
import sys
import io
import base64
from pathlib import Path
try:
    from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps
except ImportError:
    sys.exit("Pillow is required:  python -m pip install Pillow")
THEMES = {
    "dark": ("#39d353", "#0e4429", None),
    "light": ("#216e39", "#aceebb", None),
}
ASCII_RAMP = "@%#*+=-:. "
BRAILLE_BASE = 0x2800
BRAILLE_BITS = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]
def square_crop(img, fx: float, fy: float):
    w, h = img.size
    side = min(w, h)
    left = min(max(fx * w - side / 2, 0), w - side)
    top = min(max(fy * h - side / 2, 0), h - side)
    return img.crop((round(left), round(top), round(left) + side, round(top) + side))
def load_grid(path: Path, cols: int, contrast: float, gamma: float,
              cell_aspect: float, square: bool = False,
              focus: tuple[float, float] = (0.5, 0.5),
              equalize: bool = False, detail: float = 0.0):
    img = ImageOps.exif_transpose(Image.open(path))
    
    # Keep the image with alpha for embedding if needed
    embed_img = img.copy()
    if embed_img.mode not in ("RGB", "RGBA"):
        embed_img = embed_img.convert("RGBA")
        
    mask = None
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        if img.split()[3].getextrema()[0] < 250:
            mask = img.split()[3]
        flat = Image.new("RGBA", img.size, (0, 0, 0, 255))
        flat.alpha_composite(img)
        img = flat
    img = img.convert("RGB")
    if square:
        img = square_crop(img, *focus)
        embed_img = square_crop(embed_img, *focus)
        if mask is not None:
            mask = square_crop(mask, *focus)
    gray = img.convert("L")
    if equalize:
        binmask = mask.point(lambda v: 255 if v > 127 else 0) if mask else None
        gray = ImageOps.equalize(gray, mask=binmask)
    if detail > 0:
        radius = max(2, round(min(img.size) / 52))
        gray = gray.filter(ImageFilter.UnsharpMask(
            radius=radius, percent=round(detail * 100), threshold=0))
    if contrast != 1.0:
        gray = ImageEnhance.Contrast(gray).enhance(contrast)
        img = ImageEnhance.Contrast(img).enhance(contrast)
        embed_img = ImageEnhance.Contrast(embed_img).enhance(contrast)
    w, h = img.size
    rows = max(1, round(cols * (h / w) * cell_aspect))
    small_g = gray.resize((cols, rows), Image.Resampling.LANCZOS)
    if mask is not None:
        small_m = mask.resize((cols, rows), Image.Resampling.LANCZOS)
        small_g = ImageChops.multiply(small_g, small_m)
    small_c = img.resize((cols, rows), Image.Resampling.LANCZOS)
    gp, cp = small_g.load(), small_c.load()
    rgb, lum = [], []
    for y in range(rows):
        rgb_row, lum_row = [], []
        for x in range(cols):
            rgb_row.append(cp[x, y])
            v = gp[x, y] / 255.0
            lum_row.append(min(1.0, max(0.0, v ** gamma)))
        rgb.append(rgb_row)
        lum.append(lum_row)
    return cols, rows, lum, rgb, embed_img
def get_base64_image(img: Image.Image) -> str:
    buffered = io.BytesIO()
    if img.mode == "RGBA":
        img.save(buffered, format="PNG")
        mime = "image/png"
    else:
        img.save(buffered, format="JPEG", quality=85)
        mime = "image/jpeg"
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:{mime};base64,{img_str}"
def circle_falloff(x, y, cols, rows, feather=0.06):
    nx = (x + 0.5) / cols * 2 - 1
    ny = (y + 0.5) / rows * 2 - 1
    d = math.hypot(nx, ny)
    if d <= 1 - feather:
        return 1.0
    if d >= 1 + feather:
        return 0.0
    return (1 + feather - d) / (2 * feather)
def svg_header(w, h, rows, opts):
    css = []
    if opts.animate:
        css.append("@keyframes dp{0%,100%{opacity:.45}50%{opacity:1}}")
        css.append(f".d{{animation:dp {opts.duration}s ease-in-out infinite}}")
        css += [f".l{i}{{animation-delay:{i / opts.lanes * opts.duration:.2f}s}}"
                for i in range(opts.lanes)]
    if opts.reveal:
        step = opts.reveal_time / max(rows - 1, 1)
        css.append("@keyframes rv{from{opacity:0}to{opacity:1}}")
        css.append(f".rw{{animation:rv {opts.reveal_fade}s ease-out both}}")
        css += [
            f".r{y}{{animation-delay:{(rows - 1 - y if opts.reveal_dir == 'up' else y) * step:.3f}s}}"
            for y in range(rows)
        ]
    if opts.embed_image:
        css.append("@keyframes fIn{from{opacity:0;filter:blur(8px)}to{opacity:1;filter:blur(0)}}")
        css.append(f".clear-img{{animation:fIn {opts.embed_duration}s ease-out forwards;animation-delay:{opts.embed_delay}s;opacity:0}}")
        if opts.dots_fade_out:
            css.append("@keyframes fOut{from{opacity:1}to{opacity:0}}")
            css.append(f".dots-group{{animation:fOut {opts.embed_duration}s ease-in-out forwards;animation-delay:{opts.embed_delay}s}}")
    style = f"<style>{''.join(css)}</style>" if css else ""
    bgrect = f'<rect width="100%" height="100%" fill="{opts.bg}"/>' if opts.bg else ""
    pad = opts.pad
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {w + 2 * pad} {h + 2 * pad}" '
        f'width="{w + 2 * pad}" height="{h + 2 * pad}" role="img" '
        f'aria-label="dot-matrix portrait">{style}{bgrect}'
        f'<g transform="translate({pad},{pad})">'
    )
def build_dots(cols, rows, lum, rgb, theme, opts):
    fg, dim, _ = THEMES[theme]
    cell = opts.cell
    max_r = cell * 0.5 * opts.dot_scale
    lanes = opts.lanes
    out = []
    for y in range(rows):
        row = []
        for x in range(cols):
            v = lum[y][x]
            if opts.invert:
                v = 1 - v
            if opts.circle:
                v *= circle_falloff(x, y, cols, rows)
            if v < opts.floor:
                continue
            r = max_r * (v ** 0.85)
            if r < 0.18:
                continue
            cx = x * cell + cell / 2
            cy = y * cell + cell / 2
            if opts.color:
                cr, cg, cb = rgb[y][x]
                fill = f"#{cr:02x}{cg:02x}{cb:02x}"
            else:
                fill = fg if v > 0.42 else dim
            cls = f' class="d l{x % lanes}"' if opts.animate else ""
            row.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.2f}" fill="{fill}"{cls}/>'
            )
        if not row:
            continue
        if opts.reveal:
            out.append(f'<g class="rw r{y}">{"".join(row)}</g>')
        else:
            out += row
    return "".join(out), cols * cell, rows * cell
def build_binary(cols, rows, lum, rgb, theme, opts):
    fg, dim, _ = THEMES[theme]
    cell = opts.cell
    lanes = opts.lanes
    out = [
        f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
        f'font-size="{cell * 0.92:.2f}" text-anchor="middle">'
    ]
    for y in range(rows):
        row = []
        for x in range(cols):
            v = lum[y][x]
            if opts.invert:
                v = 1 - v
            if opts.circle:
                v *= circle_falloff(x, y, cols, rows)
            if v < opts.floor:
                continue
            bit = "1" if ((x * 7 + y * 13 + int(v * 37)) % 3) else "0"
            if v > 0.62:
                bit = "1"
            if opts.color:
                cr, cg, cb = rgb[y][x]
                fill = f"#{cr:02x}{cg:02x}{cb:02x}"
            else:
                fill = fg if v > 0.42 else dim
            cls = f' class="d l{x % lanes}"' if opts.animate else ""
            op = f' opacity="{0.25 + 0.75 * v:.2f}"'
            row.append(
                f'<text x="{x * cell + cell / 2:.1f}" y="{y * cell + cell * 0.82:.1f}" '
                f'fill="{fill}"{op}{cls}>{bit}</text>'
            )
        if not row:
            continue
        if opts.reveal:
            out.append(f'<g class="rw r{y}">{"".join(row)}</g>')
        else:
            out += row
    out.append("</g>")
    return "".join(out), cols * cell, rows * cell
def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image", type=Path, help="source photo (jpg/png/webp)")
    p.add_argument("-o", "--out", type=Path, default=Path("assets/portrait"),
                   help="output path WITHOUT extension (default: assets/portrait)")
    p.add_argument("--mode", choices=("dots", "binary"), default="dots")
    p.add_argument("--cols", type=int, default=88, help="dots across (default 88)")
    p.add_argument("--cell", type=float, default=10.0, help="SVG units per cell")
    p.add_argument("--dot-scale", type=float, default=0.92)
    p.add_argument("--gamma", type=float, default=1.0)
    p.add_argument("--contrast", type=float, default=1.25)
    p.add_argument("--equalize", action="store_true")
    p.add_argument("--detail", type=float, default=0.0)
    p.add_argument("--floor", type=float, default=0.06)
    p.add_argument("--cell-aspect", type=float, default=1.0)
    p.add_argument("--square", action="store_true")
    p.add_argument("--focus", default="0.5,0.5")
    p.add_argument("--invert", action="store_true")
    p.add_argument("--circle", action="store_true")
    p.add_argument("--color", action="store_true")
    p.add_argument("--animate", action="store_true")
    p.add_argument("--lanes", type=int, default=14)
    p.add_argument("--duration", type=float, default=4.0)
    p.add_argument("--reveal", action="store_true")
    p.add_argument("--reveal-time", type=float, default=2.5)
    p.add_argument("--reveal-fade", type=float, default=0.45)
    p.add_argument("--reveal-dir", choices=("down", "up"), default="down")
    p.add_argument("--pad", type=float, default=8.0)
    p.add_argument("--bg", default="")
    
    # New options for clear image embedding and animation
    p.add_argument("--embed-image", action="store_true", help="embed clear source image inside SVG")
    p.add_argument("--embed-delay", type=float, default=3.0, help="delay in seconds before clear image fades in")
    p.add_argument("--embed-duration", type=float, default=2.0, help="fade-in duration in seconds for clear image")
    p.add_argument("--dots-fade-out", action="store_true", help="fade out dot matrix when clear image fades in")
    
    args = p.parse_args(argv)
    if not args.image.exists():
        sys.exit(f"no such image: {args.image}")
    try:
        fx, fy = (float(v) for v in args.focus.split(","))
    except ValueError:
        sys.exit(f"--focus wants two numbers like 0.55,0.42 (got {args.focus!r})")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    cols, rows, lum, rgb, embed_img = load_grid(args.image, args.cols, args.contrast,
                                                args.gamma, args.cell_aspect,
                                                args.square, (fx, fy),
                                                args.equalize, args.detail)
    base64_uri = ""
    if args.embed_image:
        base64_uri = get_base64_image(embed_img)
        
    builder = build_dots if args.mode == "dots" else build_binary
    themes = ("dark",) if args.color else ("dark", "light")
    for theme in themes:
        body, w, h = builder(cols, rows, lum, rgb, theme, args)
        if args.embed_image:
            img_tag = f'<image class="clear-img" href="{base64_uri}" x="0" y="0" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice"/>'
            body = img_tag + f'<g class="dots-group">{body}</g>'
        svg = svg_header(w, h, rows, args) + body + "</g></svg>"
        stem = args.out.name if args.color else f"{args.out.name}-{theme}"
        dest = args.out.with_name(f"{stem}.svg")
        dest.write_text(svg, encoding="utf-8")
        print(f"wrote {dest}  ({len(svg) / 1024:.0f} KB, {cols}x{rows} cells)")
if __name__ == "__main__":
    main()
