#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"

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
CFG

echo "== tanya model sekali (harus dapat jawaban) =="
if hermes chat -q "Balas satu kata saja: siap" -Q; then
  echo "MODEL-JAWAB"
else
  echo "MODEL-GAGAL:$?"
fi

echo "== jembatan antrean =="
export CF_ACCOUNT CF_TOKEN CF_DB_UUID
python3 k0.py
echo "JEMBATAN-SELESAI"

echo "== selesai =="
