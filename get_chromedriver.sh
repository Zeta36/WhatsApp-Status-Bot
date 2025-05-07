#!/usr/bin/env bash
set -euo pipefail

# ⇩ 1) Ajusta solo esta variable si cambias de ruta
TARGET_DIR="/home/user/path/to/whatsapp_status_bot"
TARGET_BIN="$TARGET_DIR/chromedriver"
mkdir -p "$TARGET_DIR"

# ⇩ 2) Tu major version (136). El script elegirá la última build estable 136.x
MAJOR=136

JSON="https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"

echo "🔎  Buscando ChromeDriver linux64 para major $MAJOR …"
ZIP_URL=$(curl -s "$JSON" | jq -r --arg m "$MAJOR" '
   .versions[]
   | select(.version|startswith($m+"."))
   | select(.downloads.chromedriver[]? | .platform=="linux64")
   | .downloads.chromedriver[] | select(.platform=="linux64") | .url
' | sort -V | tail -1)   # ← la build más alta del major 136

if [[ -z "$ZIP_URL" ]]; then
   echo "❌  No se encontró ChromeDriver para major $MAJOR."
   exit 1
fi
echo "⏬  Descargando $ZIP_URL"
curl -# -L "$ZIP_URL" -o /tmp/chromedriver.zip

echo "📦  Descomprimiendo…"
unzip -q /tmp/chromedriver.zip -d /tmp/chd_extracted

#  Encuentra el binario sin asumir carpeta
FOUND=$(find /tmp/chd_extracted -type f -name chromedriver | head -1)
if [[ -z "$FOUND" ]]; then
   echo "❌  No se encontró 'chromedriver' dentro del zip."
   exit 1
fi

mv "$FOUND" "$TARGET_BIN"
chmod +x "$TARGET_BIN"
rm -rf /tmp/chromedriver.zip /tmp/chd_extracted

echo "✅  ChromeDriver preparado → $TARGET_BIN"
"$TARGET_BIN" --version
