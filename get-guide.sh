#!/usr/bin/env bash
# Fetches MiniMax's H3 prompt-writing guide into the Studio's data folder (default ./data), pinned
# to a commit and checked by hash. Not kept in this repo: MiniMax's repo has no license file.
# Without it the Studio still writes the H3 format, from a short summary.
set -euo pipefail
dir=${1:-data}
url=https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/d21241f0a4b3acbb34c97dae47fa417b7065e438/skills/h3-prompt-writing/references/base-en.txt
sha=2cfebc096a6e08370f288d468d90b60f7f9bcb938f94bf090816e910e48e75fc
mkdir -p "$dir"
# -4: Hugging Face's and GitHub's CDNs hang over IPv6 on some networks.
curl -4 -fsSL --retry 3 -o "$dir/h3-prompt-guide.txt.part" "$url"
if [[ $(shasum -a 256 "$dir/h3-prompt-guide.txt.part" | cut -d' ' -f1) != "$sha" ]]; then
  rm -f "$dir/h3-prompt-guide.txt.part"
  echo "The guide doesn't match its pinned hash; not using it." >&2
  exit 1
fi
mv "$dir/h3-prompt-guide.txt.part" "$dir/h3-prompt-guide.txt"
echo "Saved $dir/h3-prompt-guide.txt"
