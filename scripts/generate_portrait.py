#!/usr/bin/env python3
import os
import io
import base64
from PIL import Image, ImageEnhance, ImageOps

def main():
    img_path = "images/kishan.png"
    if not os.path.exists(img_path):
        print(f"Error: {img_path} not found.")
        return

    # Load image kishan.png
    img = Image.open(img_path)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
        
    # Resize to 400x400 for embedding
    embed_img = img.resize((400, 400), Image.Resampling.LANCZOS)
    
    # Get base64 URI
    buffered = io.BytesIO()
    embed_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    base64_uri = f"data:image/png;base64,{img_str}"
    
    # Generate dots grid (50x50)
    cols, rows = 50, 50
    cell = 8.0
    small_img = embed_img.resize((cols, rows), Image.Resampling.LANCZOS)
    
    mask = small_img.split()[3]
    flat = Image.new("RGBA", small_img.size, (0, 0, 0, 255))
    flat.alpha_composite(small_img)
    img_rgb = flat.convert("RGB")
    gray = img_rgb.convert("L")
    
    gamma = 0.8
    enhancer = ImageEnhance.Contrast(gray)
    gray = enhancer.enhance(1.4)
    
    gp = gray.load()
    cp = img_rgb.load()
    mp = mask.load()
    
    max_r = cell * 0.5 * 0.9
    dots_out = []
    
    x_offset, y_offset = 100, 40
    
    for y in range(rows):
        row_dots = []
        for x in range(cols):
            alpha = mp[x, y]
            if alpha < 50:
                continue
            v = gp[x, y] / 255.0
            v = min(1.0, max(0.0, v ** gamma))
            v *= (alpha / 255.0)
            if v < 0.1:
                continue
            r = max_r * (v ** 0.85)
            if r < 0.5:
                continue
            cx = x_offset + x * cell + cell / 2
            cy = y_offset + y * cell + cell / 2
            cr, cg, cb = cp[x, y]
            fill = f"#{cr:02x}{cg:02x}{cb:02x}"
            row_dots.append(
                f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}"/>'
            )
        if row_dots:
            dots_out.append((y, "".join(row_dots)))
            
    # CSS rules
    css = []
    # Dots reveal
    css.append("""
@keyframes rv {
  from { opacity: 0; }
  to { opacity: 1; }
}
.rw {
  animation: rv 0.20s ease-out both;
}""")
    for y in range(rows):
        css.append(f".r{y} {{ animation-delay: {y * 0.020:.3f}s; }}")
        
    # Dots fade out
    css.append("""
@keyframes fOut {
  from { opacity: 1; }
  to { opacity: 0; }
}
.dots-group {
  animation: fOut 1.0s ease-in-out forwards;
  animation-delay: 1.5s;
}""")
    
    # Clear image fade in
    css.append("""
@keyframes fIn {
  from { opacity: 0; filter: blur(8px); }
  to { opacity: 1; filter: blur(0); }
}
.clear-img {
  animation: fIn 1.2s ease-out forwards;
  animation-delay: 1.5s;
  opacity: 0;
}""")

    # Text reveal
    css.append("""
@keyframes textReveal {
  from { opacity: 0; transform: translateY(15px); filter: blur(4px); }
  to { opacity: 1; transform: translateY(0); filter: blur(0); }
}
.name-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 32px;
  font-weight: bold;
  text-anchor: middle;
  animation: textReveal 0.8s ease-out both;
  animation-delay: 2.2s;
}
.title-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 20px;
  text-anchor: middle;
  animation: textReveal 0.8s ease-out both;
  animation-delay: 2.7s;
}
@media (prefers-color-scheme: dark) {
  .name-text { fill: #ffffff; }
  .title-text { fill: #8b949e; }
}
@media (prefers-color-scheme: light) {
  .name-text { fill: #24292f; }
  .title-text { fill: #57606a; }
}
""")

    # Dots markup
    dots_markup_list = []
    for y, row_content in dots_out:
        dots_markup_list.append(f'<g class="rw r{y}">{row_content}</g>')
    dots_markup = "\n  ".join(dots_markup_list)
    
    style_block = f"<style>{''.join(css)}</style>"
    
    svg_content = f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" width="600px" height="600px" viewBox="0 0 600 600">
{style_block}
<!-- Clear Image -->
<image class="clear-img" href="{base64_uri}" x="{x_offset}" y="{y_offset}" width="400" height="400" preserveAspectRatio="xMidYMid slice"/>

<!-- Dots Group -->
<g class="dots-group">
  {dots_markup}
</g>

<!-- Animated Text -->
<text class="name-text" x="300" y="490">Kishan C Bhandary</text>
<text class="title-text" x="300" y="535">Developer | Software Engineer</text>
</svg>
"""
    
    os.makedirs("assets", exist_ok=True)
    with open("assets/portrait.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Successfully generated assets/portrait.svg!")

if __name__ == "__main__":
    main()
