#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess

def convert_to_avif(src, dst):
    cmd = [
        'ffmpeg', '-v', 'error',
        '-i', str(src),
        '-y',
        '-c:v', 'libaom-av1',
        '-crf', '48',
        '-b:v', '0',
        '-cpu-used', '0',
        str(dst)
    ]
    return subprocess.run(cmd).returncode == 0

def main():
    src_dir = Path('input')
    dst_dir = Path('output')
    dst_dir.mkdir(exist_ok=True)
    
    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.avif'}
    files = [f for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() in exts]
    
    if not files:
        print("❌ No supported image files in input directory")
        return

    total = len(files)
    done = 0

    for i, f in enumerate(files, 1):
        out = dst_dir / (f.stem + '_Low_Quality.avif')
        print(f'\r🔄 [{i}/{total}] Processing: {f.name}', end='', flush=True)
        
        if convert_to_avif(f, out):
            done += 1
            orig_mb = f.stat().st_size / 1024 / 1024
            avif_mb = out.stat().st_size / 1024 / 1024
            ratio = avif_mb / orig_mb  # size ratio
            print(f'\r✅ [{i}/{total}] {f.name} → {orig_mb:.3f} MB → {avif_mb:.3f} MB ({ratio:.2f}x)')
        else:
            print(f'\r❌ [{i}/{total}] {f.name} conversion failed')

    print(f"\n🎉 Done! Success: {done}/{total}")

if __name__ == '__main__':
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, check=True)
    except:
        print("❌ Please install ffmpeg")
        exit(1)
    main()