#!/usr/bin/env python3
import os
import sys
import argparse
import html
from PIL import Image

# Supported image extensions
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tiff')

# Standard monospace characters ramp, ordered from dark (dense) to bright (space)
# This mapping ensures dark subject areas become visible characters and bright
# background areas wash out to spaces (which reveal the dark SVG background).
DEFAULT_RAMP = "@#$8%*o=+-;:. "

def load_and_preprocess_image(image_path, target_width=100, aspect_ratio_adjust=0.55):
    """
    Load an image, composite it onto a white background to handle transparency,
    convert it to grayscale, and resize it with aspect ratio correction.
    """
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image: {e}", file=sys.stderr)
        sys.exit(1)
        
    # Handle transparency by compositing on white
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        # Convert P to RGBA if necessary
        img_rgba = img.convert("RGBA")
        bg.paste(img_rgba, (0, 0), img_rgba)
        img_gray = bg.convert("L")
    else:
        img_gray = img.convert("L")
        
    # Calculate target dimensions with font aspect ratio correction
    orig_w, orig_h = img_gray.size
    aspect_ratio = orig_w / orig_h
    target_height = int(round((target_width / aspect_ratio) * aspect_ratio_adjust))
    target_height = max(1, target_height)
    
    # Resize using high-quality Lanczos resampling
    img_resized = img_gray.resize((target_width, target_height), Image.Resampling.LANCZOS)
    return img_resized

def convert_to_ascii(img, ramp):
    """
    Convert a grayscale image to a list of ASCII character strings.
    """
    ascii_rows = []
    w, h = img.size
    
    for y in range(h):
        row = ""
        for x in range(w):
            val = img.getpixel((x, y))
            # Map pixel values [0, 255] to ramp indices [0, len(ramp)-1]
            idx = int(val / 256.0 * len(ramp))
            row += ramp[idx]
        ascii_rows.append(row)
        
    return ascii_rows

def generate_animated_svg(ascii_rows, output_path, title, args):
    """
    Generate an animated SVG using SMIL showing text typing line-by-line.
    """
    num_rows = len(ascii_rows)
    num_cols = len(ascii_rows[0]) if num_rows > 0 else 0
    
    # Calculate dimensions
    char_width = args.char_width
    font_size = args.font_size
    line_height = args.line_height
    
    padding_x = args.padding_x
    padding_y = args.padding_y
    header_height = args.header_height
    
    W = num_cols * char_width
    svg_width = int(W + 2 * padding_x)
    svg_height = int(header_height + num_rows * line_height + 2 * padding_y)
    
    # Animation settings
    start_delay = args.delay
    row_dur = args.row_duration
    
    # Find the last non-empty row and the position of its last character for final blinking cursor
    last_non_empty_idx = -1
    last_non_empty_len = 0
    for idx in range(num_rows - 1, -1, -1):
        stripped = ascii_rows[idx].rstrip()
        if len(stripped) > 0:
            last_non_empty_idx = idx
            last_non_empty_len = len(stripped)
            break
            
    # Build clip paths, texts, and cursors
    clip_paths = []
    text_elements = []
    cursors = []
    
    for i, row in enumerate(ascii_rows):
        t_start = start_delay + i * row_dur
        t_end = t_start + row_dur
        
        # Calculate Y positions
        y_top = header_height + padding_y + i * line_height
        y_baseline = y_top + font_size - 1
        
        # Escape row content for XML safely
        escaped_row = html.escape(row)
        
        # 1. Clip path for this row (reveals text left-to-right)
        clip_paths.append(f"""    <clipPath id="clip_{i}">
      <rect x="{padding_x}" y="{y_top}" width="0" height="{line_height}">
        <animate attributeName="width" from="0" to="{W:.2f}" begin="{t_start:.3f}s" dur="{row_dur:.3f}s" fill="freeze" />
      </rect>
    </clipPath>""")
        
        # 2. Text element for this row
        text_elements.append(
            f'  <text xml:space="preserve" class="ascii-text" x="{padding_x}" y="{y_baseline:.2f}" '
            f'clip-path="url(#clip_{i})" textLength="{W:.2f}">{escaped_row}</text>'
        )
        
        # 3. Cursor for this row (sweeps across row during typing and then disappears)
        cursors.append(f"""  <rect class="cursor-rect" x="{padding_x}" y="{y_top}" width="{char_width:.2f}" height="{line_height}" fill="{args.cursor_color}" opacity="0">
    <animate attributeName="opacity" values="1;1;0" keyTimes="0;0.95;1" begin="{t_start:.3f}s" dur="{row_dur:.3f}s" fill="freeze" />
    <animate attributeName="x" from="{padding_x}" to="{padding_x + W:.2f}" begin="{t_start:.3f}s" dur="{row_dur:.3f}s" fill="freeze" />
  </rect>""")

    # 4. Final blinking cursor at the end of the text
    t_final_start = start_delay + num_rows * row_dur
    if last_non_empty_idx >= 0:
        final_cx = padding_x + last_non_empty_len * char_width
        final_cy = header_height + padding_y + last_non_empty_idx * line_height
        final_cursor = f"""  <!-- Final blinking cursor -->
  <rect class="cursor-rect" x="{final_cx:.2f}" y="{final_cy}" width="{char_width:.2f}" height="{line_height}" fill="{args.cursor_color}" opacity="0">
    <animate attributeName="opacity" values="0;1;0" keyTimes="0;0.5;1" begin="{t_final_start:.3f}s" dur="1.0s" repeatCount="indefinite" />
  </rect>"""
    else:
        final_cursor = ""

    # Assemble the SVG contents
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%" style="max-width: {svg_width}px; background-color: {args.bg_color}; border-radius: 8px; box-shadow: 0 12px 40px rgba(0,0,0,0.5); overflow: hidden;">
  <style>
    .ascii-text {{
      font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: {font_size}px;
      fill: {args.text_color};
      font-weight: 500;
    }}
    .window-dot {{
      stroke: rgba(0, 0, 0, 0.15);
      stroke-width: 1px;
    }}
    .terminal-title {{
      font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
      fill: #8b949e;
    }}
  </style>

  <!-- Definitions for animations -->
  <defs>
{chr(10).join(clip_paths)}
  </defs>

  <!-- Terminal Window Background -->
  <rect width="100%" height="100%" fill="{args.bg_color}" />

  <!-- Terminal Header Bar -->
  <rect width="100%" height="{header_height}" fill="{args.header_color}" />

  <!-- Window controls (macOS style window dots) -->
  <circle class="window-dot" cx="20" cy="20" r="6" fill="#ff5f56" />
  <circle class="window-dot" cx="40" cy="20" r="6" fill="#ffbd2e" />
  <circle class="window-dot" cx="60" cy="20" r="6" fill="#27c93f" />

  <!-- Terminal Title -->
  <text class="terminal-title" x="85" y="25">{html.escape(title)}</text>

  <!-- ASCII Art Rows -->
{chr(10).join(text_elements)}

  <!-- Typing Cursors -->
{chr(10).join(cursors)}

{final_cursor}
</svg>
"""

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        print(f"Successfully generated animated SVG at: {output_path}")
    except Exception as e:
        print(f"Error saving SVG: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Convert any image to an animated ASCII terminal SVG.")
    parser.add_argument("image", nargs="?", help="Path to input image. If omitted, the script auto-detects the newest image in ~/Downloads/ascii.")
    parser.add_argument("--width", type=int, default=100, help="Width of ASCII art in characters (default: 100).")
    parser.add_argument("--font-size", type=int, default=14, help="Font size in pixels (default: 14).")
    parser.add_argument("--char-width", type=float, default=8.4, help="Character width in pixels for monospace font (default: 8.4).")
    parser.add_argument("--line-height", type=float, default=15.0, help="Line height/vertical spacing in pixels (default: 15.0).")
    parser.add_argument("--row-duration", type=float, default=0.08, help="Duration to type each row in seconds (default: 0.08).")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay before typing begins in seconds (default: 0.5).")
    parser.add_argument("--bg-color", default="#0d1117", help="Background color of terminal (default: #0d1117).")
    parser.add_argument("--header-color", default="#161b22", help="Header bar color of terminal (default: #161b22).")
    parser.add_argument("--text-color", default="#e6edf3", help="Text/character color (default: #e6edf3).")
    parser.add_argument("--cursor-color", default="#58a6ff", help="Block cursor color (default: #58a6ff).")
    parser.add_argument("--padding-x", type=int, default=25, help="Horizontal padding (default: 25).")
    parser.add_argument("--padding-y", type=int, default=20, help="Vertical padding below header (default: 20).")
    parser.add_argument("--header-height", type=int, default=40, help="Height of window header bar (default: 40).")
    parser.add_argument("--invert", action="store_true", help="Invert the character ramp mapping (light pixels map to dense characters).")
    
    args = parser.parse_args()
    
    # 1. Determine the image path
    image_path = None
    
    # Check ~/Downloads/ascii
    downloads_dir = os.path.expanduser("~/Downloads")
    ascii_dir = os.path.join(downloads_dir, "ascii")
    
    # Create the folder if it doesn't exist
    folder_created = False
    if not os.path.exists(ascii_dir):
        try:
            os.makedirs(ascii_dir, exist_ok=True)
            print(f"Created directory: {ascii_dir}")
            folder_created = True
        except Exception as e:
            print(f"Error creating directory {ascii_dir}: {e}", file=sys.stderr)
            sys.exit(1)
            
    if args.image:
        image_path = args.image
        if not os.path.exists(image_path):
            print(f"Error: Specified image file does not exist: {image_path}", file=sys.stderr)
            sys.exit(1)
    else:
        # Auto-detect image in ~/Downloads/ascii
        try:
            files = [os.path.join(ascii_dir, f) for f in os.listdir(ascii_dir)]
            image_files = [f for f in files if os.path.isfile(f) and f.lower().endswith(IMAGE_EXTENSIONS)]
        except Exception as e:
            print(f"Error reading directory {ascii_dir}: {e}", file=sys.stderr)
            sys.exit(1)
            
        if not image_files:
            if folder_created:
                print(f"Please drop an image file (PNG, JPG, WebP, etc.) into the newly created folder:\n  {ascii_dir}\nand run this script again.", file=sys.stderr)
            else:
                print(f"No image files found in:\n  {ascii_dir}\nPlease drop an image file there or specify a path as an argument.", file=sys.stderr)
            sys.exit(1)
            
        # Get the newest image by modification time
        image_path = max(image_files, key=os.path.getmtime)
        print(f"Auto-detected newest image: {image_path}")

    # Determine title (displayed in the terminal header)
    base_name = os.path.basename(image_path)
    title = f"kishan@terminal: ~/ascii/{base_name}"
    
    # Determine output path (replace extension with .svg next to the image)
    dir_name = os.path.dirname(image_path)
    file_no_ext, _ = os.path.splitext(base_name)
    output_path = os.path.join(dir_name, f"{file_no_ext}.svg")
    
    # 2. Process image and generate ASCII
    print("Loading and preprocessing image...")
    preprocessed_img = load_and_preprocess_image(image_path, target_width=args.width)
    
    # Handle character ramp inversion
    ramp = DEFAULT_RAMP
    if args.invert:
        ramp = DEFAULT_RAMP[::-1]
        
    print(f"Converting to ASCII art (using character ramp mapping)...")
    ascii_rows = convert_to_ascii(preprocessed_img, ramp)
    
    # 3. Generate animated SVG
    print("Generating animated SVG...")
    generate_animated_svg(ascii_rows, output_path, title, args)

if __name__ == "__main__":
    main()
