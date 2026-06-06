#!/bin/zsh
# Headless screenshots of all key states. Usage: shots.sh [base-url] [outdir]
set -e
BASE=${1:-http://localhost:4173}
OUT=${2:-/tmp/velger-qa}
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
mkdir -p "$OUT"
shot() {  # name url width height
  # Run Chrome in background; kill after 30s if still running (WebGL startup guard).
  # Note: macOS has no `timeout` in base install; use background-kill pattern.
  # --force-device-scale-factor=1 ensures layout pixel = device pixel in headless shots.
  "$CHROME" --headless=new --hide-scrollbars --force-device-scale-factor=1 \
    --screenshot="$OUT/$1.png" --window-size=$3,$4 \
    --user-data-dir="$OUT/profile-$1" "$2" 2>/dev/null &
  local pid=$!
  local waited=0
  while kill -0 $pid 2>/dev/null && (( waited < 30 )); do
    sleep 1; (( waited++ ))
  done
  kill $pid 2>/dev/null || true
  wait $pid 2>/dev/null || true
  echo "$OUT/$1.png"
}
shot landing      "$BASE/"                 1440 900
shot orbit        "$BASE/?qa=orbit"        1440 900
shot exploded     "$BASE/?qa=exploded"     1440 900
shot floor2       "$BASE/?qa=floor2"       1440 900
shot panel        "$BASE/?qa=unit-H0204"   1440 900
shot mobil        "$BASE/?qa=exploded"     390  844
shot mobil-panel  "$BASE/?qa=unit-H0204"   390  844
