#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$ROOT/pdfs}"
mkdir -p "$OUT"

fetch() {
  local id="$1"
  local name="$2"
  local dest="$OUT/${id}-${name}.pdf"
  if [[ -s "$dest" ]]; then
    printf 'exists  %s\n' "$dest"
    return
  fi
  printf 'fetch   arXiv:%s -> %s\n' "$id" "$dest"
  curl --fail --location --retry 3 --retry-delay 2 \
    --user-agent 'climbhill-research/1.0' \
    "https://arxiv.org/pdf/${id}" \
    --output "$dest"
}

fetch 2608.18066 fragility
fetch 2606.19980 enpire
fetch 2608.16590 zetta
fetch 2607.07663 recursive-self-improvement
fetch 2608.16859 harnesseval-w
fetch 2608.17588 truss
fetch 2607.01942 atomic-task-graph
fetch 2608.16889 baton
fetch 2608.16055 governance-boundary
fetch 2608.16246 composkill
fetch 2608.16071 skill2query

printf '\nDownloaded PDFs to %s\n' "$OUT"
