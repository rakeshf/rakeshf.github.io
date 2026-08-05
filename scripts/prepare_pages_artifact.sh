#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-_site}"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

shopt -s nullglob

for file in *.html *.png *.ico robots.txt sitemap.xml symbols.txt sentiment.txt darvas-box.txt; do
  if [ -f "$file" ]; then
    cp "$file" "$OUT_DIR/"
  fi
done

for dir in css js data; do
  if [ -d "$dir" ]; then
    cp -R "$dir" "$OUT_DIR/"
  fi
done
