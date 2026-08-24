#!/usr/bin/env python3
import subprocess
import shutil
import os

def main():
    img_path = "images/kishan.png"
    if not os.path.exists(img_path):
        print(f"Error: {img_path} not found.")
        return

    # Run ascii_terminal.py to generate images/kishan.svg
    print("Running ascii_terminal.py on images/kishan.png...")
    subprocess.run([".venv/bin/python", "ascii_terminal.py", img_path], check=True)
    
    # Copy images/kishan.svg to assets/portrait.svg
    os.makedirs("assets", exist_ok=True)
    shutil.copy("images/kishan.svg", "assets/portrait.svg")
    print("Successfully copied images/kishan.svg to assets/portrait.svg!")

if __name__ == "__main__":
    main()
