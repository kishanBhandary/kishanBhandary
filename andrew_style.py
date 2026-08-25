#!/usr/bin/env python3
import os
import sys
from PIL import Image, ImageEnhance

# 1. Image Preprocessing & ASCII Art Generation
def generate_animated_portrait_assets():
    img_path = "images/kishan.png"
    if not os.path.exists(img_path):
        print(f"Error: {img_path} not found.")
        sys.exit(1)
        
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
    
    # Align to the left column: x_offset = 15, y_offset = 85 (vertically centered in 530px card height)
    x_offset, y_offset = 15, 85
    
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
    
    dots_markup_list = []
    for y, row_content in dots_out:
        dots_markup_list.append(f'<g class="rw r{y}">{row_content}</g>')
    dots_markup = "\n  ".join(dots_markup_list)
    
    # CSS rules for portrait
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

    return dots_markup, ascii_markup, "".join(css)

# Helper function to generate dotted leaders alignment
def get_leader_line(key, value, total_cols=32):
    # Prefix is ". " (2 chars)
    # Key + ":"
    key_part = f"{key}:"
    used_len = 2 + len(key_part)
    dots_len = total_cols - used_len
    dots = "." * max(1, dots_len)
    
    # Format with SVG tspans
    return f'<tspan class="cc">. </tspan><tspan class="key">{key}</tspan>:<tspan class="cc"> {dots} </tspan><tspan class="value">{value}</tspan>'

def generate_svg(mode, dots_markup, ascii_markup, portrait_css):
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
        # Line 1: Header
        f'<tspan x="390" y="30">kishan@bhandary</tspan> -———————————————————————————————————————————-——',
        
        # Section 1: System Info
        f'<tspan x="390" y="50">{get_leader_line("OS", "Linux,Fedora,KaliLinux,MintLinux, Ubuntu")}</tspan>',
        f'<tspan x="390" y="70">{get_leader_line("Uptime", "21 years, 7 months, 20 days")}</tspan>',
        f'<tspan x="390" y="90">{get_leader_line("Host", "AJ Institute of Engineering &amp; Tech")}</tspan>',
        f'<tspan x="390" y="110">{get_leader_line("Kernel", "Information Science &amp; Engineering")}</tspan>',
        f'<tspan x="390" y="130">{get_leader_line("IDE", "VS Code, Neovim, IntelliJ")}</tspan>',
        f'<tspan x="390" y="150" class="cc">. </tspan>', # Spacer
        
        # Section 2: Languages
        f'<tspan x="390" y="170">{get_leader_line("Languages.Programming", "Python, JS, TS, Java, C++,C")}</tspan>',
        f'<tspan x="390" y="190">{get_leader_line("Languages.Markup", "HTML, CSS, SQL, SpringBoot,Nextjs,React,Supabase")}</tspan>',
        f'<tspan x="390" y="210">{get_leader_line("Languages.Real", "English, Kannada, Hindi")}</tspan>',
        f'<tspan x="390" y="230" class="cc">. </tspan>', # Spacer
        
        # Section 3: Hobbies
        f'<tspan x="390" y="250">{get_leader_line("Hobbies.Software", "Open Source, Web Dev, Automation")}</tspan>',
        f'<tspan x="390" y="270">{get_leader_line("Hobbies.Hardware", "PC Building, Arduino / IoT")}</tspan>',
        
        # Section 4: Contact
        f'<tspan x="390" y="310">- Contact</tspan> -——————————————————————————————————————————————-——',
        f'<tspan x="390" y="330">{get_leader_line("Email", "kishanbhandary0@gmail.com")}</tspan>',
        f'<tspan x="390" y="350">{get_leader_line("Website", "www.kishanbhandary.me")}</tspan>',
        f'<tspan x="390" y="370">{get_leader_line("LinkedIn", "kishan-bhandary")}</tspan>',
        f'<tspan x="390" y="390">{get_leader_line("Discord", "kishanbhandary")}</tspan>',
        f'<tspan x="390" y="410" class="cc">. </tspan>', # Spacer
        
        # Section 5: GitHub Stats
        f'<tspan x="390" y="430">- GitHub Stats</tspan> -—————————————————————————————————————————-——',
        # Hardcoded aligned lines for repos, commits, loc
        f'<tspan x="390" y="450"><tspan class="cc">. </tspan><tspan class="key">Repos</tspan>:<tspan class="cc"> .... </tspan><tspan class="value">105</tspan> {{<tspan class="key">Contributed</tspan>: <tspan class="value">70</tspan>}} | <tspan class="key">Stars</tspan>:<tspan class="cc"> ........... </tspan><tspan class="value">15</tspan></tspan>',
        f'<tspan x="390" y="470"><tspan class="cc">. </tspan><tspan class="key">Commits</tspan>:<tspan class="cc"> ................. </tspan><tspan class="value">5,248</tspan> | <tspan class="key">Followers</tspan>:<tspan class="cc"> ....... </tspan><tspan class="value">19</tspan></tspan>',
        f'<tspan x="390" y="490"><tspan class="cc">. </tspan><tspan class="key">Lines of Code on GitHub</tspan>:<tspan class="cc">. </tspan><tspan class="value">78,412</tspan> ( <tspan class="key" style="fill: #3fb950 if mode == "dark" else "#1a7f37";">85,214</tspan>++, <tspan style="fill: #f85149 if mode == "dark" else "#cf222e";">6,802</tspan>-- )</tspan>',
        f'<tspan x="390" y="510" class="cc">. </tspan><tspan style="fill: #3fb950 if mode == "dark" else "#1a7f37";">kishan@bhandary</tspan><tspan>:~$ </tspan><tspan class="blinking-cursor">█</tspan>',
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

    # Assemble the SVG contents
    svg_content = f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="985px" height="530px" font-size="16px">
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
.blinking-cursor {{
  animation: blink 1s step-start infinite;
  fill: {cursor_color};
}}
@keyframes blink {{
  50% {{ opacity: 0; }}
}}
text, tspan {{ white-space: pre; }}
{portrait_css}
</style>
<rect width="985px" height="530px" fill="{bg_color}" rx="15"/>

<!-- ASCII Portrait -->
<text class="clear-img" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" font-size="10px" text-anchor="middle" font-weight="900">
  {ascii_markup}
</text>

<!-- Dots Group -->
<g class="dots-group">
  {dots_markup}
</g>

<text x="390" y="30" fill="{text_color}">
{chr(10).join(info_lines)}
</text>
</svg>
"""
    return svg_content

def main():
    print("Generating animated portrait assets...")
    dots_markup, ascii_markup, portrait_css = generate_animated_portrait_assets()
    
    print("Generating dark_mode.svg...")
    dark_svg = generate_svg("dark", dots_markup, ascii_markup, portrait_css)
    with open("dark_mode.svg", "w", encoding="utf-8") as f:
        f.write(dark_svg)
        
    print("Generating light_mode.svg...")
    light_svg = generate_svg("light", dots_markup, ascii_markup, portrait_css)
    with open("light_mode.svg", "w", encoding="utf-8") as f:
        f.write(light_svg)
        
    print("Generating README.md...")
    import time
    version = int(time.time())
    readme_content = f"""<p align="center">
  <img src="assets/portrait.svg?v={version}" alt="Kishan C Bhandary Portrait" width="1200">
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="dark_mode.svg?v={version}">
    <source media="(prefers-color-scheme: light)" srcset="light_mode.svg?v={version}">
    <img alt="Kishan Bhandary Profile Card" src="dark_mode.svg?v={version}" width="985" height="530">
  </picture>
</p>

---

<h3 align="center"><i>Social Media Handles</i></h3>

<table align="center">
<tr>
    <td align="center" width="60">
        <a href="https://www.instagram.com/">
            <img src="https://cdn-icons-png.flaticon.com/512/1409/1409946.png" width="60" alt="Instagram">
        </a>
    </td>
    <td align="center" width="60">
        <a href="https://www.linkedin.com/in/kishan-c-bhandary-476375297/">
            <img src="https://cdn-icons-png.flaticon.com/512/1409/1409945.png" width="60" alt="LinkedIn">
        </a>
    </td>
    <td align="center" width="60">
        <a href="https://kishanbhandary.me">
            <img src="https://cdn-icons-png.flaticon.com/512/1006/1006771.png" width="60" alt="Portfolio">
        </a>
    </td>
</tr>
</table>

## About Me 

📍 Based in Mangalore, I’m currently pursuing my degree in Information Science at AJ Institute of Engineering and Technology. I’m an enthusiastic learner with a strong passion for technology, especially in the areas of web development and software engineerin.

I’m constantly exploring new tools, frameworks, and technologies to enhance my skills and contribute to impactful projects. Whether it’s building efficient backend systems or crafting intuitive front-end interfaces, I enjoy turning ideas into real-world solutions. 

[![An image of @kishanbhandary's Holopin badges, which is a link to view their full Holopin profile](https://holopin.me/kishanbhandary)](https://holopin.io/@kishanbhandary)
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    print("SVG assets and README.md generated successfully!")

if __name__ == "__main__":
    main()
