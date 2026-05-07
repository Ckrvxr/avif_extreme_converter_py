#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess

def convert_to_jxl(src, dst):
    cmd = [
        'ffmpeg', '-v', 'error',
        '-i', str(src),
        '-y',
        '-c:v', 'libjxl',
        '-distance', '0',
        '-effort', '9',
        str(dst)
    ]
    return subprocess.run(cmd).returncode == 0

def main():
    src_dir = Path('input')
    dst_dir = Path('output')
    dst_dir.mkdir(exist_ok=True)
    
    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.avif', '.jxl'}
    files = [f for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() in exts]
    
    if not files:
        print("❌ No supported image files in input directory")
        return

    total = len(files)
    done = 0

    print(f"🚀 Starting JXL Lossless conversion (Effort 9)...")
    for i, f in enumerate(files, 1):
        out = dst_dir / (f.stem + '_Lossless.jxl')
        print(f'\r🔄 [{i}/{total}] Processing: {f.name}', end='', flush=True)
        
        if convert_to_jxl(f, out):
            done += 1
            orig_size = f.stat().st_size
            jxl_size = out.stat().st_size
            saved = (1 - jxl_size / orig_size) * 100
            print(f'\r✅ [{i}/{total}] {f.name} → {orig_size/1024/1024:.2f}MB → {jxl_size/1024/1024:.2f}MB (Saved: {saved:.1f}%)')
        else:
            print(f'\r❌ [{i}/{total}] {f.name} conversion failed')

    print(f"\n🎉 Done! Success: {done}/{total}")

if __name__ == '__main__':
    try:
        res = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
        if 'libjxl' not in res.stdout:
            print("❌ ffmpeg 'libjxl' encoder missing")
            exit(1)
    except:
        print("❌ ffmpeg not found")
        exit(1)
    main()