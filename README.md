# Studio

From a brief to finished video shots on your own GPU: a chat model writes the shot list,
Krea 2 makes each shot's first frame, MiniMax H3 animates it with sound, SeedVR2 or a plain
upscale takes it to 1080p, and the result goes to DaVinci Resolve as clips plus an EDL.

It runs on [ComfyUI](https://github.com/comfyanonymous/ComfyUI) (on its own or inside
SwarmUI) and any OpenAI-compatible chat API (Ollama, LM Studio, llama-server). Together with
[gpu-switcher](https://github.com/sjespersen/gpu-switcher) it shares one GPU with the chat
models: it asks for the GPU per job and holds it while it works. It came out of
[homelab-agent](https://github.com/sjespersen/homelab-agent), where it runs on a GPU box.

Only the Python standard library, one process, projects as JSON files.

## The steps

1. **Brief and characters.** Describe the film, and give each recurring person one clear photo
   (showing the outfit, on a plain background: the photo's background leaks into the stills
   otherwise). **Write shot list** has a chat model turn it into shots: a still prompt (the
   first frame) and a motion-and-sound prompt per shot. Edit any of it, or add shots by hand.
   Motion prompts follow H3's own format (`integrated_multimodal_description`,
   `overall_soundscape`, `non_diegetic_music`; the Studio adds the first-frame line): the model
   gets MiniMax's [H3 prompt-writing guide](https://github.com/MiniMax-AI/MiniMax-H3/tree/main/skills/h3-prompt-writing)
   with the brief. **Rewrite for H3** turns a prompt you wrote in plain words into that format.
   Each project picks its chat model under the brief (`STUDIO_LLM` is the default for new
   projects). Small models (8-14B) work but write weaker H3 prompts.

   **Or start from a picture**: drop one under the brief and say what should happen. A model
   that can see (Qwen3.8 or Gemma 3, for example) reads the place, each person's outfit,
   position and box, and a prompt for the picture. The shot list then starts with the picture as
   shot 1's still, and the people become characters. Krea makes each person a full-body
   reference photo on a plain background and an image of each place, so one picture builds the
   whole project.

   The model also writes the film's **places and outfits** once, and each shot names its place
   and, per person, an outfit and where they stand in the frame.
2. **Stills**: Krea 2 Turbo makes each shot's first frame at the final size, with the place's
   and the outfits' descriptions in every prompt, so the room and the clothes stay the same
   from shot to shot. With characters in the shot it uses the
   [Krea 2 Identity Edit V2](https://huggingface.co/conradlocke/krea2-identity-edit) LoRA with
   their photos, one pass per person. Krea doesn't know names, so the Studio swaps them for
   positions ("the person on the left"). **LoRAs** under the brief adds Krea 2 LoRAs from the
   models folder, each with a strength. A new one starts at a suggested strength: the Studio
   measures how hard each LoRA changes the model's weights (they differ by 30× and more), and
   scales the strong ones down so they don't smear the picture. A row set well above it offers
   the suggestion, and a warning shows when the LoRAs together push too hard.
3. **Previews**: MiniMax H3 animates the still at ~0.3 MP (736×416 for 16:9), with sound.
   **Video LoRAs** adds H3 LoRAs. The Studio tells them from Krea 2 ones by their headers.
4. **Review**: approve, retry (a new seed) or reject each preview; only approved ones go on.
5. **Finals**: the approved preview again (same seed, frame, prompt and LoRAs, so the same
   motion), its latent upscaled by a learned H3 upscaler and refined at H3's full size
   (1344×768).
6. **Upscale** to 1080p: **Clean** (the default: Lanczos only, ~20 s, nothing invented),
   **Soft** (SeedVR2 3B mixed with a plain upscale) or **SeedVR2** alone (the most detail, and
   invented skin texture that can shift between chunks). Long clips are upscaled in ~7.7 s
   pieces and joined, so RAM stays under ~45 GB.
7. **Export for Resolve**: a zip with the clips in order, `timeline.edl` (File > Import >
   Timeline) and the prompts.

Jobs run one at a time, grouped by kind so models load less often.

Measured on an RTX 5060 Ti 16 GB with 64 GB RAM, for one 6.6-second 16:9 shot:

| Step | Time | Peak VRAM / RAM |
|---|---|---|
| Still (Krea 2 + identity LoRA) | ~50 s | — |
| Preview (736×416) | 1½ min | 15.8 / 11 GB |
| Final (1344×768) | 5½ min | 15.6 / 18 GB |
| Upscale (1920×1080), Clean | ~20 s | — |
| Upscale, Soft or SeedVR2 | 10 min | — / ~45 GB for long clips |

So a finished minute of film is roughly 1¼ hours of GPU time after you approve the previews.
It needs an NVIDIA card with 16 GB. On a Mac (ComfyUI on MPS), expect the stills to work, but
slowly; H3 video at these sizes is unlikely to be practical.

## Run it

You need ComfyUI with the [models](#models) and the two [node packs](#comfyui-node-packs), a
chat API, and `API_KEY` (any long random string: the page's login).

**With Docker**, next to an existing ComfyUI:

```yaml
services:
  studio:
    image: ghcr.io/sjespersen/studio:latest
    environment:
      API_KEY: ${API_KEY}
      SWITCHER: ""                                  # or http://switcher:8079 with gpu-switcher
      LLM_URL: http://host.docker.internal:11434/v1  # Ollama on the host
      COMFY_URL: http://host.docker.internal:8188
    volumes:
      - ./data:/data                  # projects (back this up)
      - ./media:/media                # renders
      - ~/ComfyUI/models:/models:ro   # only to see which models are there
      - ~/ComfyUI:/comfy/ComfyUI      # optional: lets it delete ComfyUI's copies of its files
    ports:
      - "127.0.0.1:8078:8078"
    extra_hosts: ["host.docker.internal:host-gateway"]
```

**Without Docker** (Python 3.11 or newer):

```sh
python3 guide.py data   # MiniMax's H3 prompt guide, optional
API_KEY=$(openssl rand -hex 24) SWITCHER= LISTEN=127.0.0.1 \
  DATA=data MEDIA=media MODELS=~/ComfyUI/models COMFY_DIR=~/ComfyUI \
  LLM_URL=http://127.0.0.1:11434/v1 COMFY_URL=http://127.0.0.1:8188 python3 app.py
```

Then open `http://127.0.0.1:8078`.

## Settings

| Setting | Default | What |
|---|---|---|
| `API_KEY` | (required) | The page's login; also the Bearer token for gpu-switcher |
| `SWITCHER` | `http://switcher:8079` | gpu-switcher's address. Empty: no switcher; you start ComfyUI and the chat model yourself. With one, the jobs ask it for its image service (`kind: image`) and the chosen chat model |
| `LLM_URL`, `LLM_KEY` | `http://127.0.0.1:11434/v1` | The chat API without a switcher (with one, the switcher's `/v1` and its Ollama) |
| `STUDIO_LLM` | `qwen3.8-flash-next` | The chat model for new projects |
| `COMFY_URL` | `http://swarmui:7801/ComfyBackendDirect` | ComfyUI's API: plain ComfyUI (`http://127.0.0.1:8188`) or SwarmUI's pass-through |
| `COMFY_DIR` | `/comfy/ComfyUI` | ComfyUI's folder, to delete its copies of uploads and renders (skipped if missing) |
| `MODELS` | `/models` | ComfyUI's or SwarmUI's models folder, read-only |
| `DATA`, `MEDIA` | `/data`, `/media` | Projects (small, back them up); renders (large) |
| `LISTEN`, `PORT` | `0.0.0.0`, `8078` | Where the page listens. Use `127.0.0.1` outside a container |

The page's login is the same cookie gpu-switcher uses, so behind one address (homelab-agent
sends `/_ai/*` to the switcher) one login covers both.

## Models

The page lists what's missing. Folder names are SwarmUI's; plain ComfyUI's `loras` and `vae`
work too. Hugging Face's CDN stalls over IPv6 on some networks, so download with
`curl -4 -L -C -`:

| File | Folder | From |
|---|---|---|
| `krea2_turbo_fp8_scaled`, `qwen3vl_4b`, `QwenImage/qwen_image_vae` | `diffusion_models`, `text_encoders`, `VAE` | [Comfy-Org/Krea-2](https://huggingface.co/Comfy-Org/Krea-2) (SwarmUI fetches the last two itself the first time you use Krea 2) |
| `krea2_identity_edit_v2` | `Lora` | [conradlocke/krea2-identity-edit](https://huggingface.co/conradlocke/krea2-identity-edit) |
| `minimax_h3_fl2va_pruned_w6a8`, `qwen3vl_32b_minimax_h3_nvfp4_awq`, `minimax_h3_video_vae_int8_convrot`, `minimax_h3_audio_vae_fp32`, `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16` | `diffusion_models`, `text_encoders`, `VAE`, `VAE`, `Lora` | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) |
| `minimax_h3_latent_upscaler_3d_conv_v1_bf16` | `latent_upscale_models` | [LBH-123-AI/Minimax_h3_latent_Upscaler](https://huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler) |
| `seedvr2_3b_int8_convrot`, `seedvr2_ema_vae_fp16` | `diffusion_models`, `VAE` | [Comfy-Org/SeedVR2](https://huggingface.co/Comfy-Org/SeedVR2) |

## ComfyUI node packs

Pinned in [`comfy-nodes.txt`](comfy-nodes.txt): clone each into ComfyUI's `custom_nodes` and
check out its commit ([comfyui-krea2edit](https://github.com/lbouaraba/comfyui-krea2edit) for
the identity LoRA, [the H3 latent upscaler](https://github.com/xmarre/Comfyui_Minimax_h3_latent_Upscaler-Plus)).
Both were read before pinning: no network calls, no subprocesses, no installs at runtime.

```sh
while read -r name repo commit; do
  [[ -n $name && $name != \#* ]] || continue
  git clone -q "$repo" ~/ComfyUI/custom_nodes/"$name" && git -C ~/ComfyUI/custom_nodes/"$name" checkout -q "$commit"
done <comfy-nodes.txt
```

## Your own instructions

The instructions to the models (`SHOT_PROMPT`, `REWRITE_PROMPT`, `MOTION_FORMAT`,
`PICTURE_PROMPT` in `app.py`) are defaults. A file `DATA/prompts/<NAME>.txt` replaces one,
read on each use, so your own versions stay with your projects, out of git.

`guide.py` fetches MiniMax's H3 prompt guide into `DATA` (pinned to a commit and checked by
hash; not kept here, since its repository has no license). Without it the model still writes
the format from a short summary.

## Licenses

The Studio is MIT. The models are not: MiniMax H3's license excludes the US, UK, EU and South
Korea unless MiniMax authorizes you (apply on their H3 license page). The identity LoRA is
free for personal, non-commercial use only. The H3 upscaler's repository and MiniMax's H3
repository have no license.
