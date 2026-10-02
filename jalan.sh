#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"

# antrean kosong = keluar hening sebelum buang waktu pasang
if [ -n "${CF_ACCOUNT:-}" ]; then
  if python3 - <<'CEK'
import json, os, urllib.request
try:
    url = ("https://api.cloudflare.com/client/v4/accounts/%s/d1/database/%s/query"
           % (os.environ["CF_ACCOUNT"], os.environ["CF_DB_UUID"]))
    badan = json.dumps({"sql": "SELECT COUNT(*) AS n FROM agen_perintah WHERE status='menunggu'"}).encode()
    req = urllib.request.Request(url, data=badan, headers={
        "Authorization": "Bearer " + os.environ["CF_TOKEN"],
        "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        n = json.loads(r.read())["result"][0]["results"][0]["n"]
except Exception as e:
    print("DIAG cek gagal:", str(e)[:160])
    n = 1  # gagal cek = jalankan saja (aman: k0.py baca ulang)
print("DIAG n =", repr(n), "uuid_len =", len(os.environ.get("CF_DB_UUID","")), "acct_len =", len(os.environ.get("CF_ACCOUNT","")))
raise SystemExit(0 if n == 0 else 1)
CEK
  then
    echo "antrean kosong"
    exit 0
  fi
fi

echo "== pasang =="
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --non-interactive --skip-browser --skip-computer-use

echo "== siapkan konfigurasi provider =="
mkdir -p "$HOME/.hermes"
cat > "$HOME/.hermes/config.yaml" <<CFG
model:
  default: deepseek-v4.1-flash
  provider: bariska
  api_mode: chat_completions
  base_url: https://api.bariska.cloud/v1
providers:
  bariska:
    api: https://api.bariska.cloud/v1
    name: Bariska
    api_key: ${KUNCI_PROVIDER}
    transport: chat_completions
    default_model: deepseek-v4.1-flash
fallback_providers:
  - provider: bariska
    model: glm-5.3-flash
  - provider: bariska
    model: qwen3.8-flash
  - provider: bariska
    model: auto
CFG

echo "== jembatan antrean =="
export CF_ACCOUNT CF_TOKEN CF_DB_UUID
python3 k0.py
echo "JEMBATAN-SELESAI"
