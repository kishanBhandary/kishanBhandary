#!/usr/bin/env python3
import os
import sys
from PIL import Image, ImageEnhance

# 1. Image Preprocessing & ASCII Art Generation
def generate_ascii_art():
    img_path = "images/kishan-removebg-preview.png"
    if not os.path.exists(img_path):
        print(f"Error: {img_path} not found.")
        sys.exit(1)
        
    img = Image.open(img_path)
    
    # Composite on white background for transparency
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img_rgba = img.convert("RGBA")
        bg.paste(img_rgba, (0, 0), img_rgba)
        img_gray = bg.convert("L")
    else:
        img_gray = img.convert("L")
        
    # Crop tight to the face (centered on horizontal axis 246)
    # Width: 300px, Height: 310px
    crop_box = (96, 44, 396, 354)
    img_cropped = img_gray.crop(crop_box)
    
    # Lift shadows using gamma correction (gamma = 0.6)
    gamma = 0.6
    lut = [int(255 * (i / 255.0) ** gamma) for i in range(256)]
    img_lifted = img_cropped.point(lut)
    
    # Increase contrast to make facial details pop
    enhancer = ImageEnhance.Contrast(img_lifted)
    img_enhanced = enhancer.enhance(1.6)
    
    # Resize to exact grid for SVG (44 columns, 25 rows)
    img_resized = img_enhanced.resize((44, 25), Image.Resampling.LANCZOS)
    
    # Map to safe ASCII ramp
    ramp = "@#$8%*o=+-;:. "
    ascii_rows = []
    for y in range(img_resized.height):
        row = ""
        for x in range(img_resized.width):
            val = img_resized.getpixel((x, y))
            idx = int(val / 256.0 * len(ramp))
            row += ramp[idx]
        ascii_rows.append(row)
        
    return ascii_rows

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

def generate_svg(mode, ascii_rows):
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
        
    # Build ASCII tspans (on the left column, x=15)
    ascii_tspans = []
    for i, row in enumerate(ascii_rows):
        y_pos = 30 + i * 20
        ascii_tspans.append(f'<tspan x="15" y="{y_pos}">{row}</tspan>')
        
    # Build Info tspans (on the right column, x=390)
    info_lines = [
        # Line 1: Header
        f'<tspan x="390" y="30">kishan@bhandary</tspan> -———————————————————————————————————————————-——',
        
        # Section 1: System Info
        f'<tspan x="390" y="50">{get_leader_line("OS", "Linux (Ubuntu 24.04 LTS)")}</tspan>',
        f'<tspan x="390" y="70">{get_leader_line("Uptime", "21 years, 7 months, 20 days")}</tspan>',
        f'<tspan x="390" y="90">{get_leader_line("Host", "AJ Institute of Engineering &amp; Tech")}</tspan>',
        f'<tspan x="390" y="110">{get_leader_line("Kernel", "Information Science &amp; Engineering")}</tspan>',
        f'<tspan x="390" y="130">{get_leader_line("IDE", "VS Code, Neovim, IntelliJ")}</tspan>',
        f'<tspan x="390" y="150" class="cc">. </tspan>', # Spacer
        
        # Section 2: Languages
        f'<tspan x="390" y="170">{get_leader_line("Languages.Programming", "Python, JS, TS, Go, C++")}</tspan>',
        f'<tspan x="390" y="190">{get_leader_line("Languages.Markup", "HTML, CSS, SQL, Markdown")}</tspan>',
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
        f'<tspan x="390" y="450"><tspan class="cc">. </tspan><tspan class="key">Repos</tspan>:<tspan class="cc"> .... </tspan><tspan class="value">45</tspan> {{<tspan class="key">Contributed</tspan>: <tspan class="value">18</tspan>}} | <tspan class="key">Stars</tspan>:<tspan class="cc"> ........... </tspan><tspan class="value">15</tspan></tspan>',
        f'<tspan x="390" y="470"><tspan class="cc">. </tspan><tspan class="key">Commits</tspan>:<tspan class="cc"> ................. </tspan><tspan class="value">1,248</tspan> | <tspan class="key">Followers</tspan>:<tspan class="cc"> ....... </tspan><tspan class="value">19</tspan></tspan>',
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
</style>
<rect width="985px" height="530px" fill="{bg_color}" rx="15"/>
<text x="15" y="30" fill="{text_color}" class="ascii">
{chr(10).join(ascii_tspans)}
</text>
<text x="390" y="30" fill="{text_color}">
{chr(10).join(info_lines)}
</text>
</svg>
"""
    return svg_content

def main():
    print("Generating ASCII self-portrait...")
    ascii_rows = generate_ascii_art()
    
    print("Generating dark_mode.svg...")
    dark_svg = generate_svg("dark", ascii_rows)
    with open("dark_mode.svg", "w", encoding="utf-8") as f:
        f.write(dark_svg)
        
    print("Generating light_mode.svg...")
    light_svg = generate_svg("light", ascii_rows)
    with open("light_mode.svg", "w", encoding="utf-8") as f:
        f.write(light_svg)
        
    print("Generating README.md...")
    readme_content = """# Hi there! 👋

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="dark_mode.svg">
  <source media="(prefers-color-scheme: light)" srcset="light_mode.svg">
  <img alt="Kishan Bhandary Profile Card" src="dark_mode.svg" width="985" height="530">
</picture>

---

*This profile README was automatically generated with an identical design to Andrew6rant's profile.*
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    print("SVG assets and README.md generated successfully!")

if __name__ == "__main__":
    main()
