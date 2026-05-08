#!/usr/bin/env python3
import os
import tempfile
from pathlib import Path
import subprocess

SCRIPT_DIR = Path(__file__).resolve().parent

def compress_with_zopfli(src, dst):
    temp_png = None
    input_path = str(src)

    if src.suffix.lower() != '.png':
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_png = temp_file.name
        temp_file.close()
        
        conv_cmd = ['ffmpeg', '-v', 'error', '-i', str(src), '-y', temp_png]
        if subprocess.run(conv_cmd).returncode != 0:
            return False
        input_path = temp_png

    zop_cmd = [
        'zopflipng', '-y', '--lossy_transparent', '--iterations=15',
        input_path, str(dst)
    ]
    result = subprocess.run(zop_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if temp_png and os.path.exists(temp_png):
        os.remove(temp_png)

    return result.returncode == 0

def main():
    src_dir = SCRIPT_DIR.parent / 'input'
    dst_dir = SCRIPT_DIR.parent / 'output'
    dst_dir.mkdir(exist_ok=True)
    
    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.avif', '.heic', '.heif', '.jxl'}
    files = [f for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() in exts]
    
    if not files:
        print("❌ No supported files found in input directory")
        return

    total = len(files)
    done = 0

    print(f"🚀 Starting Hybrid Zopfli Compression...")
    for i, f in enumerate(files, 1):
        out = dst_dir / (f.stem + '_Optimized.png')
        print(f'\r🔄 [{i}/{total}] Processing: {f.name}', end='', flush=True)
        
        if compress_with_zopfli(f, out):
            done += 1
            orig_size = f.stat().st_size
            opt_size = out.stat().st_size
            saved = (1 - opt_size / orig_size) * 100
            print(f'\r✅ [{i}/{total}] {f.name} → {orig_size/1024:.1f}KB → {opt_size/1024:.1f}KB ({saved:.1f}%)')
        else:
            print(f'\r❌ [{i}/{total}] {f.name} failed')

    print(f"\n🎉 Done! Success: {done}/{total}")

if __name__ == '__main__':
    try:
        subprocess.run(['zopflipng', '--help'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("❌ Ensure both 'zopflipng' and 'ffmpeg' are installed")
        exit(1)
    main()