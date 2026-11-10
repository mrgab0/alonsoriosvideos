#!/usr/bin/env bash
# ffmpeg_overlay.sh
# Superpone una imagen con canal alfa sobre un video (sin animación frame a frame).
#
# Uso:
#   bash scripts/ffmpeg_overlay.sh input.mp4 overlay.png output.mp4

set -euo pipefail

INPUT="${1:?Falta el video de entrada}"
OVERLAY="${2:?Falta la imagen con transparencia}"
OUTPUT="${3:?Falta el video de salida}"

ffmpeg -y -i "$INPUT" -i "$OVERLAY" \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto" \
  -c:a copy \
  -c:v libx264 -crf 18 -preset medium \
  "$OUTPUT"

echo "[+] Renderizado: $OUTPUT"
