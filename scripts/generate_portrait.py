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
        
    # Resize to 360x360 for embedding
    embed_img = img.resize((360, 360), Image.Resampling.LANCZOS)
    
    # Generate dots grid (45x45)
    cols, rows = 45, 45
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
    
    # Canvas is 985x530. Center of 985 is 492.5.
    x_offset, y_offset = 312.5, 25
    
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
            
    # Generate ASCII portrait markup
    ramp = "@#$8%*o=+-;:. "
    ascii_markup_list = []
    for y in range(rows):
        for x in range(cols):
            alpha = mp[x, y]
            if alpha < 50:
                continue
            val = gp[x, y]
            idx = int(val / 256.0 * len(ramp))
            char = ramp[idx]
            if char == " ":
                continue
            cx = x_offset + x * cell + cell / 2
            cy_text = y_offset + y * cell + cell / 2 + 3.0
            cr, cg, cb = cp[x, y]
            fill = f"#{cr:02x}{cg:02x}{cb:02x}"
            
            escaped_char = char
            if char == "<": escaped_char = "&lt;"
            elif char == ">": escaped_char = "&gt;"
            elif char == "&": escaped_char = "&amp;"
            
            ascii_markup_list.append(
                f'<tspan x="{cx:.2f}" y="{cy_text:.2f}" fill="{fill}">{escaped_char}</tspan>'
            )
    ascii_markup = "".join(ascii_markup_list)
            
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

    # Text reveal keyframes
    css.append("""
@keyframes charAnim {
  0% { opacity: 0; filter: blur(3px); }
  100% { opacity: 1; filter: blur(0); }
}
@keyframes colorFlashDark {
  0% { fill: #39ff14; }
  50% { fill: #39ff14; }
  100% { fill: #ffffff; }
}
@keyframes colorFlashLight {
  0% { fill: #2da44e; }
  50% { fill: #2da44e; }
  100% { fill: #24292f; }
}
@keyframes titleFlashDark {
  0% { fill: #39ff14; }
  50% { fill: #39ff14; }
  100% { fill: #8b949e; }
}
@keyframes titleFlashLight {
  0% { fill: #2da44e; }
  50% { fill: #2da44e; }
  100% { fill: #57606a; }
}
.name-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 36px;
  font-weight: bold;
  text-anchor: middle;
}
.title-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 20px;
  text-anchor: middle;
}
@media (prefers-color-scheme: dark) {
  .nc {
    animation: charAnim 0.6s cubic-bezier(0.16, 1, 0.3, 1) both, colorFlashDark 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
  }
  .tc {
    animation: charAnim 0.5s cubic-bezier(0.16, 1, 0.3, 1) both, titleFlashDark 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
  }
}
@media (prefers-color-scheme: light) {
  .nc {
    animation: charAnim 0.6s cubic-bezier(0.16, 1, 0.3, 1) both, colorFlashLight 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
  }
  .tc {
    animation: charAnim 0.5s cubic-bezier(0.16, 1, 0.3, 1) both, titleFlashLight 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
  }
}
""")

    # Staggered delays for name characters (starting at 2.0s)
    name = "Kishan C Bhandary"
    name_xml = []
    for i, c in enumerate(name):
        char_str = c if c != " " else "&#160;"
        name_xml.append(f'<tspan class="nc n{i}">{char_str}</tspan>')
        delay = 2.0 + i * 0.045
        css.append(f".n{i} {{ animation-delay: {delay:.3f}s, {delay:.3f}s; }}")
        
    # Staggered delays for title characters (starting at 2.8s)
    title = "Developer | Software Engineer"
    title_xml = []
    for i, c in enumerate(title):
        char_str = c if c != " " else "&#160;"
        title_xml.append(f'<tspan class="tc t{i}">{char_str}</tspan>')
        delay = 2.8 + i * 0.025
        css.append(f".t{i} {{ animation-delay: {delay:.3f}s, {delay:.3f}s; }}")

    dots_markup_list = []
    for y, row_content in dots_out:
        dots_markup_list.append(f'<g class="rw r{y}">{row_content}</g>')
    dots_markup = "\n  ".join(dots_markup_list)
    
    style_block = f"<style>{''.join(css)}</style>"
    
    svg_content = f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" width="985px" height="530px" viewBox="0 0 985 530">
{style_block}
<!-- ASCII Portrait -->
<text class="clear-img" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="10px" text-anchor="middle" font-weight="900">
  {ascii_markup}
</text>

<!-- Dots Group -->
<g class="dots-group">
  {dots_markup}
</g>

<!-- Animated Text -->
<text class="name-text" x="492.5" y="440">{"".join(name_xml)}</text>
<text class="title-text" x="492.5" y="485">{"".join(title_xml)}</text>
</svg>
"""
    
    os.makedirs("assets", exist_ok=True)
    with open("assets/portrait.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Successfully generated assets/portrait.svg!")

if __name__ == "__main__":
    main()
