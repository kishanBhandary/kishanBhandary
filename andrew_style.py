#!/usr/bin/env python3
import os
import sys
import io
import base64
import time
from PIL import Image, ImageEnhance, ImageOps

# 1. Generate Dot Portrait Elements and Base64 URI
def generate_portrait_elements(img_path, cols=40, rows=45, x_offset=25, y_offset=85, cell=8.0):
    if not os.path.exists(img_path):
        print(f"Error: {img_path} not found.")
        sys.exit(1)
        
    img = Image.open(img_path)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
        
    # Resize to target dots grid
    small_img = img.resize((cols, rows), Image.Resampling.LANCZOS)
    
    # Resize to display resolution for base64 embedding
    display_w = cols * cell
    display_h = rows * cell
    embed_img = img.resize((int(display_w), int(display_h)), Image.Resampling.LANCZOS)
    
    # Get base64 URI
    buffered = io.BytesIO()
    embed_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    base64_uri = f"data:image/png;base64,{img_str}"
    
    # Generate dots
    dots_out = []
    
    # Calculate luminance using alpha weighting
    mask = small_img.split()[3]
    # Composite on black background for grayscale calculation
    flat = Image.new("RGBA", small_img.size, (0, 0, 0, 255))
    flat.alpha_composite(small_img)
    img_rgb = flat.convert("RGB")
    gray = img_rgb.convert("L")
    
    # Boost contrast and apply gamma
    gamma = 0.8
    enhancer = ImageEnhance.Contrast(gray)
    gray = enhancer.enhance(1.4)
    
    gp = gray.load()
    cp = img_rgb.load()
    mp = mask.load()
    
    max_r = cell * 0.5 * 0.9  # Dot scale of 0.9
    
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
            
    return dots_out, base64_uri, int(display_w), int(display_h)

# Helper function to generate dotted leaders alignment
def get_leader_line(key, value, total_cols=32):
    key_part = f"{key}:"
    used_len = 2 + len(key_part)
    dots_len = total_cols - used_len
    dots = "." * max(1, dots_len)
    return f'<tspan class="cc">. </tspan><tspan class="key">{key}</tspan>:<tspan class="cc"> {dots} </tspan><tspan class="value">{value}</tspan>'

def generate_svg(mode, dots_out, base64_uri, display_w, display_h, x_offset, y_offset, rows):
    if mode == "dark":
        bg_color = "#161b22"
        text_color = "#c9d1d9"
        key_color = "#ffa657"
        value_color = "#a5d6ff"
        dots_color = "#616e7f"
        cursor_color = "#39ff14"
    else:
        bg_color = "#f6f8fa"
        text_color = "#24292f"
        key_color = "#953800"
        value_color = "#0a3069"
        dots_color = "#c2cfde"
        cursor_color = "#2da44e"
        
    # Build Info tspans (on the right column, x=390)
    info_lines = [
        # Section 1: System Info
        f'<tspan class="det d0" x="390" y="30"><tspan style="fill: {text_color}; font-weight: bold;">kishan@bhandary</tspan> -———————————————————————————————————————————-——</tspan>',
        f'<tspan class="det d1" x="390" y="50">{get_leader_line("OS", "Linux,Fedora,KaliLinux,MintLinux, Ubuntu")}</tspan>',
        f'<tspan class="det d2" x="390" y="70">{get_leader_line("Uptime", "21 years, 7 months, 20 days")}</tspan>',
        f'<tspan class="det d3" x="390" y="90">{get_leader_line("Host", "AJ Institute of Engineering &amp; Tech")}</tspan>',
        f'<tspan class="det d4" x="390" y="110">{get_leader_line("Kernel", "Information Science &amp; Engineering")}</tspan>',
        f'<tspan class="det d5" x="390" y="130">{get_leader_line("IDE", "VS Code, Neovim, IntelliJ")}</tspan>',
        f'<tspan class="det d6 cc" x="390" y="150">. </tspan>', # Spacer
        
        # Section 2: Languages
        f'<tspan class="det d7" x="390" y="170">{get_leader_line("Languages.Programming", "Python, JS, TS, Java, C++,C")}</tspan>',
        f'<tspan class="det d8" x="390" y="190">{get_leader_line("Languages.Markup", "HTML, CSS, SQL, SpringBoot,Nextjs,React,Supabase")}</tspan>',
        f'<tspan class="det d9" x="390" y="210">{get_leader_line("Languages.Real", "English, Kannada, Hindi")}</tspan>',
        f'<tspan class="det d10 cc" x="390" y="230">. </tspan>', # Spacer
        
        # Section 3: Hobbies
        f'<tspan class="det d11" x="390" y="250">{get_leader_line("Hobbies.Software", "Open Source, Web Dev, Automation")}</tspan>',
        f'<tspan class="det d12" x="390" y="270">{get_leader_line("Hobbies.Hardware", "PC Building, Arduino / IoT")}</tspan>',
        f'<tspan class="det d13 cc" x="390" y="290">. </tspan>', # Spacer
        
        # Section 4: Contact
        f'<tspan class="det d14" x="390" y="310">- Contact -——————————————————————————————————————————————-——</tspan>',
        f'<tspan class="det d15" x="390" y="330">{get_leader_line("Email", "kishanbhandary0@gmail.com")}</tspan>',
        f'<tspan class="det d16" x="390" y="350">{get_leader_line("Website", "www.kishanbhandary.me")}</tspan>',
        f'<tspan class="det d17" x="390" y="370">{get_leader_line("LinkedIn", "kishan-bhandary")}</tspan>',
        f'<tspan class="det d18" x="390" y="390">{get_leader_line("Discord", "kishanbhandary")}</tspan>',
        f'<tspan class="det d19 cc" x="390" y="410">. </tspan>', # Spacer
        
        # Section 5: GitHub Stats
        f'<tspan class="det d20" x="390" y="430">- GitHub Stats -—————————————————————————————————————————-——</tspan>',
        f'<tspan class="det d21" x="390" y="450"><tspan class="cc">. </tspan><tspan class="key">Repos</tspan>:<tspan class="cc"> .... </tspan><tspan class="value">105</tspan> {{<tspan class="key">Contributed</tspan>: <tspan class="value">70</tspan>}} | <tspan class="key">Stars</tspan>:<tspan class="cc"> ........... </tspan><tspan class="value">15</tspan></tspan>',
        f'<tspan class="det d22" x="390" y="470"><tspan class="cc">. </tspan><tspan class="key">Commits</tspan>:<tspan class="cc"> ................. </tspan><tspan class="value">5,248</tspan> | <tspan class="key">Followers</tspan>:<tspan class="cc"> ....... </tspan><tspan class="value">19</tspan></tspan>',
        f'<tspan class="det d23" x="390" y="490"><tspan class="cc">. </tspan><tspan class="key">Lines of Code on GitHub</tspan>:<tspan class="cc">. </tspan><tspan class="value">78,412</tspan> ( <tspan class="key" style="fill: #3fb950 if mode == "dark" else "#1a7f37";">85,214</tspan>++, <tspan style="fill: #f85149 if mode == "dark" else "#cf222e";">6,802</tspan>-- )</tspan>',
        f'<tspan class="det d24" x="390" y="510"><tspan class="cc">. </tspan><tspan style="fill: #3fb950 if mode == "dark" else "#1a7f37";">kishan@bhandary</tspan><tspan>:~$ </tspan><tspan class="blinking-cursor">█</tspan></tspan>',
    ]
    
    # Fix inline conditional strings
    for idx, line in enumerate(info_lines):
        if 'style="fill: #3fb950 if mode ==' in line:
            if mode == "dark":
                info_lines[idx] = line.replace('style="fill: #3fb950 if mode == "dark" else "#1a7f37";"', 'style="fill: #3fb950;"')
                info_lines[idx] = info_lines[idx].replace('style="fill: #f85149 if mode == "dark" else "#cf222e";"', 'style="fill: #f85149;"')
            else:
                info_lines[idx] = line.replace('style="fill: #3fb950 if mode == "dark" else "#1a7f37";"', 'style="fill: #1a7f37;"')
                info_lines[idx] = info_lines[idx].replace('style="fill: #f85149 if mode == "dark" else "#cf222e";"', 'style="fill: #cf222e;"')

    # Build css rules
    css_rules = []
    
    # Blinking cursor animation
    css_rules.append(f"""
@keyframes blink {{
  50% {{ opacity: 0; }}
}}
.blinking-cursor {{
  animation: blink 1s step-start infinite;
  fill: {cursor_color};
}}""")

    # Dots reveal animation
    css_rules.append("""
@keyframes rv {
  from { opacity: 0; }
  to { opacity: 1; }
}
.rw {
  animation: rv 0.20s ease-out both;
}""")

    # Dots row delays
    for y in range(rows):
        css_rules.append(f".r{y} {{ animation-delay: {y * 0.025:.3f}s; }}")

    # Dots fade out
    css_rules.append("""
@keyframes fOut {
  from { opacity: 1; }
  to { opacity: 0; }
}
.dots-group {
  animation: fOut 1.0s ease-in-out forwards;
  animation-delay: 1.5s;
}""")

    # Clear image fade in
    css_rules.append("""
@keyframes fIn {
  from { opacity: 0; filter: blur(8px); }
  to { opacity: 1; filter: blur(0); }
}
.clear-img {
  animation: fIn 1.2s ease-out forwards;
  animation-delay: 1.5s;
  opacity: 0;
}""")

    # Details reveal animation
    css_rules.append("""
@keyframes fInText {
  from { opacity: 0; }
  to { opacity: 1; }
}
.det {
  animation: fInText 0.3s ease-out both;
}""")

    # Details lines delays
    for i in range(len(info_lines)):
        css_rules.append(f".d{i} {{ animation-delay: {0.4 + i * 0.06:.3f}s; }}")

    style_block = f"<style>{''.join(css_rules)}\ntext, tspan {{ white-space: pre; }}</style>"

    # Dots markup
    dots_markup_list = []
    for y, row_content in dots_out:
        dots_markup_list.append(f'<g class="rw r{y}">{row_content}</g>')
    dots_markup = "\n    ".join(dots_markup_list)

    # Assemble the SVG contents
    svg_content = f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="985px" height="530px" font-size="16px">
{style_block}
<style>
@font-face {{
  src: local('Consolas'), local('Consolas Bold');
  font-family: 'ConsolasFallback';
  font-display: swap;
  -webkit-size-adjust: 109%;
  size-adjust: 109%;
}}
.key {{ fill: {key_color}; }}
.value {{ fill: {value_color}; }}
.cc {{ fill: {dots_color}; }}
</style>
<rect width="985px" height="530px" fill="{bg_color}" rx="15"/>

<!-- Left Portrait Area -->
<!-- Clear Image -->
<image class="clear-img" href="{base64_uri}" x="{x_offset}" y="{y_offset}" width="{display_w}" height="{display_h}" preserveAspectRatio="xMidYMid slice"/>

<!-- Dots Group -->
<g class="dots-group">
  {dots_markup}
</g>

<!-- Right Details Area -->
<text x="390" y="30" fill="{text_color}">
{chr(10).join(info_lines)}
</text>
</svg>
"""
    return svg_content

def main():
    img_path = "images/kishan.png"
    print("Generating dot portrait elements and base64 uri...")
    dots_out, base64_uri, display_w, display_h = generate_portrait_elements(
        img_path, cols=40, rows=40, x_offset=25, y_offset=95, cell=8.5
    )
    
    print("Generating dark_mode.svg...")
    dark_svg = generate_svg("dark", dots_out, base64_uri, display_w, display_h, 25, 95, 40)
    with open("dark_mode.svg", "w", encoding="utf-8") as f:
        f.write(dark_svg)
        
    print("Generating light_mode.svg...")
    light_svg = generate_svg("light", dots_out, base64_uri, display_w, display_h, 25, 95, 40)
    with open("light_mode.svg", "w", encoding="utf-8") as f:
        f.write(light_svg)
        
    print("Generating README.md...")
    version = int(time.time())
    readme_content = f"""<p align="center">
  <img src="assets/portrait.svg?v={version}" alt="Kishan C Bhandary Portrait" width="400">
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="dark_mode.svg?v={version}">
    <source media="(prefers-color-scheme: light)" srcset="light_mode.svg?v={version}">
    <img alt="Kishan Bhandary Profile Card" src="dark_mode.svg?v={version}" width="985" height="530">
  </picture>
</p>

---
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    print("SVG assets and README.md generated successfully!")

if __name__ == "__main__":
    main()
