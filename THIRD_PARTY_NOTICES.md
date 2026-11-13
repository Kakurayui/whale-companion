# Third-party notices / 第三方來源聲明

本文件區分實際沿用的程式碼、僅供參考的設計、執行依賴與本機素材。資料依 2026-11-06 的來源檢查整理，2026-11-13 配合 repository 結構更新；不聲稱上游後續版本維持相同授權或行為。

## 1. surfpet — reused code and local artwork

- Repository: [Mieksido/surfpet](https://github.com/Mieksido/surfpet)
- Source revision: [`d825d236a2afb760c15b9332eee3a8ccad1958a4`](https://github.com/Mieksido/surfpet/tree/d825d236a2afb760c15b9332eee3a8ccad1958a4)
- Local asset release: [v0.2.3](https://github.com/Mieksido/surfpet/releases/tag/v0.2.3)
- Archive: [pet-pack.zip](https://github.com/Mieksido/surfpet/releases/download/v0.2.3/pet-pack.zip)
- SHA-256: `784be55efcf14d4eb633c22cb111fc13f7a13280677de266a33aec1a56e498ac`

### Code provenance

| Local file | Upstream source | Use / modifications |
|---|---|---|
| `desktop/vendor/rig.ts` | [`src/renderer/rig.ts`](https://github.com/Mieksido/surfpet/blob/d825d236a2afb760c15b9332eee3a8ccad1958a4/src/renderer/rig.ts) | Copied layered PixiJS rig, retained without modifications |
| `desktop/renderer.ts` | [`src/renderer/index.ts`](https://github.com/Mieksido/surfpet/blob/d825d236a2afb760c15b9332eee3a8ccad1958a4/src/renderer/index.ts) | Adapted pointer/gesture logic; local rig import, static shader adapter for CSP, 30 FPS limit, initial drag coordinates, double-click chat, safe error text, and our preload bridge |
| `desktop/vendor/surfpet-LICENSE.txt` | [`LICENSE`](https://github.com/Mieksido/surfpet/blob/d825d236a2afb760c15b9332eee3a8ccad1958a4/LICENSE) | Full upstream license text as received |

The received license starts with the MIT License and the copyright notice:

> Copyright (c) 2026 Derpyu520 and qq-bridge / QSH contributors

The full text is retained in [desktop/vendor/surfpet-LICENSE.txt](desktop/vendor/surfpet-LICENSE.txt). Its appended material mentions other projects and services; preservation does not mean those services are dependencies of this project. We do not use upstream SurfCore, QQ or SnowLuma services.

### Artwork provenance and distribution

`feiyu-02` (full-body) and `feiyu-03` (chibi), their layered PNGs, preview images and `assets/icon.png` come from the release above. They are **not original artwork of this project**. The original artist's separate identity and an independent art-redistribution grant were not established from the inspected release, so this notice does not invent either.

The local prototype uses these assets. The public source package excludes:

- `desktop/skins/`
- `desktop/icon.png`
- `web/feiyu/pet.png` (local preview, including any derived composite)
- local screenshots under `.work/previews/`

[tools/setup_pet_assets.py](tools/setup_pet_assets.py) restores only the two selected skins, icon and preview from the pinned upstream archive after verifying its checksum. Downloading does not itself grant redistribution rights. Obtain the applicable permissions or substitute licensed art before distributing these images, screenshots containing them, or a bundled application. See [licensing scope](docs/LICENSING.md).

Animation here is layered PNG with PixiJS, not Live2D. The project's Chinese profile and fictional setting are additions for this companion prototype and are not asserted to be official surfpet or DeepSeek lore.

## 2. AgentAtelierR — reference only

- Repository: [onion-aqua/AgentAtelierR](https://github.com/onion-aqua/AgentAtelierR)
- Reviewed revision: [`e44eb267171168da23d982ac4d3c80bf954336a8`](https://github.com/onion-aqua/AgentAtelierR/tree/e44eb267171168da23d982ac4d3c80bf954336a8)
- Use: architectural and interaction reference for coherent character experiences, persistent memory and retrieval.
- **No source code, character artwork, Spine files, audio or models were copied from AgentAtelierR.**

The inspected repository has an Apache-2.0 root license and separate media/dependency restrictions. That is a statement about the reference repository, not the license of our project. Our implementation does not include its Flutter/Spine application, event ledger or hybrid vector retrieval. Details and source links: [docs/REFERENCES.md](docs/REFERENCES.md).

## 3. Runtime and build dependencies

| Component | Version / selection | Purpose | License / terms |
|---|---|---|---|
| [Electron](https://github.com/electron/electron) | 45.0.0 | Native desktop shell | MIT; bundled Chromium and runtime components carry additional notices |
| [PixiJS](https://github.com/pixijs/pixijs) | 8.22.0 | 2D layered rendering | MIT |
| [esbuild](https://github.com/evanw/esbuild) | 0.28.2 | Renderer bundling | MIT |
| [Python](https://www.python.org/) standard library | 3.11+ | HTTP service, retrieval and SQLite persistence | Python/PSF terms; interpreter not bundled |
| [DeepSeek API](https://api-docs.deepseek.com/) | Configured hosted model; default `deepseek-flash` | External text generation | Provider's API/account terms; no model weights distributed |
| [Ollama](https://github.com/ollama/ollama) (optional) | Setup helper pins v0.40.15 | Alternative local inference | MIT runtime; not bundled |
| [Qwen3](https://github.com/QwenLM/Qwen3) (optional) | Ollama `qwen3:4b` | Alternative pretrained model | Model publisher's terms; model weights not bundled |

Node.js/npm are installation/build prerequisites. Exact npm packages, transitive versions and integrity hashes are in [desktop/package-lock.json](desktop/package-lock.json). Installed packages retain their own license files. A future binary release must retain the notices for what it actually bundles; this source package does not include `node_modules`, Electron binaries or model weights.

DeepSeek and Qwen are pretrained external models, not models trained for this project. This is not an official DeepSeek product or an endorsement by any referenced author.

## 4. Contributions in this repository

Project-specific work includes the Electron main/preload integration with Python, Chinese chat and memory editor, character prompts and fictional world text, lexical retrieval and SQLite memory workflow, local API, evaluation scenarios, scoring protocol, tests and launch/package tools. The table above identifies the surfpet-derived renderer code separately.

The earlier Mira web prototype is retained under `content/mira/` and `web/mira/`; its SVG illustration is a project asset, not a copied surfpet or AgentAtelierR image. RyzaChat:AI is contextual inspiration only; no implementation from that example has been incorporated.

The license for newly added project code has not yet been selected. Do not interpret this attribution file as a blanket license for the repository or third-party artwork.
