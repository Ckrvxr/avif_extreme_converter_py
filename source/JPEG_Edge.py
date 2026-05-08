#!/usr/bin/env python3
import sys
import re
import argparse
import tempfile
from pathlib import Path
import subprocess

SCRIPT_DIR = Path(__file__).resolve().parent
CJPEGLI = SCRIPT_DIR / 'tools' / 'jpegli' / 'build' / 'tools' / 'cjpegli'


def parse_size(s):
    s = s.strip().upper()
    m = re.match(r'^(\d+(?:\.\d+)?)\s*(KB|MB|B)?$', s)
    if not m:
        raise argparse.ArgumentTypeError(f"Invalid size format: {s}")
    val = float(m.group(1))
    unit = m.group(2) or 'B'
    if unit == 'KB':
        return int(val * 1024)
    elif unit == 'MB':
        return int(val * 1024 * 1024)
    else:
        return int(val)


def format_size(b):
    if b >= 1024 * 1024:
        return f'{b / 1024 / 1024:.2f}MB'
    elif b >= 1024:
        return f'{b / 1024:.1f}KB'
    else:
        return f'{b}B'


def encode_with_distance(src_png, dst_jpg, distance):
    cmd = [
        str(CJPEGLI), str(src_png), str(dst_jpg),
        '-d', f'{distance:.2f}',
        '--chroma_subsampling', '420',
        '-p', '2',
        '--xyb',
        '--quiet',
    ]
    return subprocess.run(cmd, capture_output=True).returncode == 0


def binary_search_distance(png_path, target_size):
    low = 0
    high = 2500
    best_d = None
    best_size = None
    size_at_d25 = None

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / 'test.jpg'

        while low <= high:
            mid = (low + high) // 2
            distance = mid / 100.0

            if not encode_with_distance(png_path, tmp_path, distance):
                return None, None

            size = tmp_path.stat().st_size
            print(f'  ⚙️  Trying distance {distance:.2f}: {format_size(size)}')
            if mid == 2500:
                size_at_d25 = size

            if size <= target_size:
                best_d = distance
                best_size = size
                high = mid - 1
            else:
                low = mid + 1

    if best_d is None and size_at_d25 is not None:
        return 0, size_at_d25

    return best_d, best_size


def main():
    if len(sys.argv) == 1:
        print("Enter parameters (separated by spaces, use default values if left empty):")
        print("  1st item: Target file size (default 500KB)")
        print("  2nd item: Maximum side pixel limit (default 0 = no limit)")
        vals = input("> ").strip().split()
        size_val = parse_size(vals[0]) if len(vals) > 0 and vals[0] else parse_size('500KB')
        max_res_val = int(vals[1]) if len(vals) > 1 and vals[1] else 0

        parser = argparse.ArgumentParser()
        parser.add_argument('--size', default=size_val)
        parser.add_argument('--max-res', type=int, default=max_res_val)
        args = parser.parse_args([])
    else:
        parser = argparse.ArgumentParser(
            description='JPEG Edge — Extreme JPEG encoding with jpegli (binary search on distance)'
        )
        parser.add_argument('--size', '--target_size', type=parse_size, required=True,
                            help='Target file size (e.g. 500KB, 2MB, 100000)')
        parser.add_argument('--max-res', type=int, default=0,
                            help='Maximum resolution in pixels (longest side), 0 = keep original')
        args = parser.parse_args()

    src_dir = Path('input')
    dst_dir = Path('output')
    dst_dir.mkdir(exist_ok=True)

    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.avif', '.heic', '.heif', '.jxl'}
    files = [f for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() in exts]

    if not files:
        print("❌ No supported image files in input directory")
        return

    total = len(files)
    done = 0
    target_label = format_size(args.size)

    resize_info = f" (max {args.max_res}px)" if args.max_res else ""
    print(f"🚀 Starting JPEG Edge encoding (target ≤ {target_label}{resize_info})...")

    for i, f in enumerate(files, 1):
        out = dst_dir / (f.stem + '_Edge.jpg')
        if args.max_res:
            print(f'🔄 [{i}/{total}] {f.name}  (max-res={args.max_res})')
        else:
            print(f'🔄 [{i}/{total}] {f.name}')

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp = Path(tmpdir)
                png_path = tmp / 'input.png'

                ffmpeg_cmd = ['ffmpeg', '-v', 'error', '-i', str(f), '-y']
                if args.max_res:
                    scale = (
                        f"scale='if(gt(iw,ih),min({args.max_res},iw),-1)':"
                        f"'if(gt(iw,ih),-1,min({args.max_res},ih))':flags=lanczos"
                    )
                    ffmpeg_cmd += ['-vf', scale]
                ffmpeg_cmd += [str(png_path)]

                if subprocess.run(ffmpeg_cmd, capture_output=True).returncode != 0:
                    print(f'❌ [{i}/{total}] {f.name}: ffmpeg decode failed')
                    continue

                best_d, best_size = binary_search_distance(
                    png_path, args.size
                )

                if best_d is None:
                    print(f'❌ [{i}/{total}] {f.name}: jpegli encoding failed')
                    continue

                if best_d == 0:
                    print(f'⚠️  [{i}/{total}] {f.name}: even distance 25.00 ({format_size(best_size)}) exceeds target {target_label}, forcing d=25.00')
                    best_d = 25.0

                if args.max_res:
                    print(f'  📋 Final parameters: distance={best_d:.2f}, max-res={args.max_res}')
                else:
                    print(f'  📋 Final parameters: distance={best_d:.2f}')
                if not encode_with_distance(png_path, out, best_d):
                    print(f'❌ [{i}/{total}] {f.name}: final encode failed')
                    continue

                done += 1
                orig_size = f.stat().st_size
                final_size = out.stat().st_size
                saved = (1 - final_size / orig_size) * 100
                print(
                    f'✅ [{i}/{total}] {f.name}  '
                    f'{format_size(orig_size)} → {format_size(final_size)}  '
                    f'(d{best_d:.2f}, target ≤ {target_label})  Saved: {saved:.1f}%'
                )
        except Exception as e:
            print(f'❌ [{i}/{total}] {f.name}: {e}')

    print(f"\n🎉 Done! Success: {done}/{total}")


if __name__ == '__main__':
    if not CJPEGLI.is_file():
        print(f"❌ cjpegli not found at {CJPEGLI}")
        print("   Build it first:")
        print(f"   cd {CJPEGLI.parent.parent.parent.parent} && cmake --build build --target cjpegli -j$(sysctl -n hw.logicalcpu)")
        exit(1)
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        print("❌ ffmpeg not found")
        exit(1)
    main()
