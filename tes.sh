#!/usr/bin/env bash
set -euo pipefail
echo "== sistem =="
uname -a
python3 --version
node --version || true
echo "== pasang (mode CI non-interaktif) =="
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --non-interactive --skip-browser --skip-computer-use
echo "== jalankan =="
export PATH="$HOME/.local/bin:$PATH"
hermes --version || true
echo "== tanya sekali (tanpa kunci provider) =="
hermes chat -q "balas satu kata: siap" -Q && echo "MODE-ONE-SHOT-JALAN" || echo "GAGAL-DI-HARAPKAN:$?"
echo "== selesai =="
