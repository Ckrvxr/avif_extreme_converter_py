#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JPEGLI_DIR="$SCRIPT_DIR/jpegli"
CJPEGLI="$JPEGLI_DIR/build/tools/cjpegli"

if [ -f "$CJPEGLI" ]; then
    echo "✅ cjpegli already built at $CJPEGLI"
    exit 0
fi

mkdir -p "$JPEGLI_DIR"

if [ ! -f "$JPEGLI_DIR/CMakeLists.txt" ]; then
    echo "📥 Cloning jpegli repository into $JPEGLI_DIR..."
    git clone --recursive https://github.com/google/jpegli.git "$JPEGLI_DIR"
else
    echo "📥 Updating submodules..."
    git -C "$JPEGLI_DIR" submodule update --init --recursive
fi

echo "🔧 Configuring cmake..."
cmake -S "$JPEGLI_DIR" -B "$JPEGLI_DIR/build" -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF

echo "🔨 Building cjpegli..."
NPROC=$(sysctl -n hw.logicalcpu 2>/dev/null || nproc 2>/dev/null || echo 4)
cmake --build "$JPEGLI_DIR/build" --target cjpegli -j"$NPROC"

echo ""
echo "✅ cjpegli built successfully!"
echo "   Binary: $CJPEGLI"
