# Working in this repo

- Commit straight to `main` and push; no feature branches or pull requests.
- This repo is public. Never commit anything about what the owner makes with the Studio: no
  project content, character names from their projects, scene examples, LoRA names or model
  names that hint at it, not in code, prompt examples, comments or commit messages. Their own
  prompts live in `data/prompts/` (gitignored). Examples in the repo stay neutral.
- Only the Python standard library: no dependencies, so the image is the app and a slim Python.
- A release is a tag `vX.Y.Z`: CI publishes `ghcr.io/sjespersen/studio`, and homelab-agent pins
  it by digest (its `update-images.sh` moves the pin).
