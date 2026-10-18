#!/data/data/com.termux/files/usr/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=== Launching AetherOS Mobile ==="

# 1. Stop any background QEMU/VNC tasks
pkill -f "qemu-system" 2>/dev/null || true
pkill -f "vncviewer" 2>/dev/null || true
pkill -x "xclock" 2>/dev/null || true

# 2. Ensure Termux:X11 is running
export DISPLAY=:0
if ! pgrep -f "termux-x11" > /dev/null; then
    echo "Starting Termux:X11 server on :0..."
    termux-x11 :0 -ac >/dev/null 2>&1 &
    sleep 2
fi

# 3. Bring Termux:X11 to front
am start --user 0 -n com.termux.x11/com.termux.x11.MainActivity >/dev/null 2>&1 || true
sleep 1

# 4. Launch AetherOS
echo "Starting AetherOS Shell..."
python3 "$DIR/src/aether_os.py"
