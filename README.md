# ComfyUI-Krea2-FlowLab

Experimental Krea-2-specific sampling nodes for ComfyUI. The project changes only the **flow integration and sigma grid**. It does **not** touch prompts, conditioning, model weights, VAE, or downstream PiD upscaling.

## What is implemented

- **K2 Advanced Sampler** — all-in-one replacement for a normal KSampler.
- **K2 Flow Sampler** — returns a standard ComfyUI `SAMPLER` object for `SamplerCustomAdvanced`.
- **K2 Native Scheduler** — produces a Krea-2 shifted flow grid from the model's own `model_sampling` configuration.

The solver performs one model evaluation per step and combines:

- variable-step Adams-Bashforth-2 history correction;
- curvature-aware fallback toward Euler when the velocity field turns sharply;
- global and local trust-region limiting of the multistep correction;
- optional middle-trajectory stochasticity using rectified-flow ancestral transport.

This is an experimental inference-time solver, not an official Krea implementation. The default `native` schedule follows the shift configured in ComfyUI; the official Krea-2 Turbo model uses shift `1.15`.

## Installation

Open a terminal in `ComfyUI/custom_nodes`:

```bash
git clone https://github.com/ekkonwork/ComfyUI-Krea2-FlowLab.git
```

Restart ComfyUI. **No `pip install` is required.** The node uses only PyTorch and modules already shipped with ComfyUI.

A successful startup contains:

```text
[K2 FlowLab] v0.1.0 loaded: K2 Advanced Sampler, K2 Flow Sampler, K2 Native Scheduler
```

### Optional installation self-check

Run from the ComfyUI root:

```bash
python custom_nodes/ComfyUI-Krea2-FlowLab/verify_install.py
```

Expected result:

```text
OK: ComfyUI imports succeeded
OK: all three nodes are registered
OK: K2 Flow Sampler produces a ComfyUI SAMPLER object
```

## Установка и первый запуск (RU)

1. Полностью закрой ComfyUI.
2. Открой терминал в папке `ComfyUI/custom_nodes`.
3. Выполни:

```bash
git clone https://github.com/ekkonwork/ComfyUI-Krea2-FlowLab.git
```

4. Запусти ComfyUI заново. Ничего устанавливать через `pip` не нужно.
5. Для твоего графа загрузи `examples/Full_QualityKrea2_K2FlowLab.json`. В нём заменён только основной sampler; prompt/conditioning, второй refine и core-нода PiD 4× сохранены.
6. Для первой проверки используй `balanced + native + eta 0`. Для контрольного результата без multistep-коррекции выбери `euler`.

Проверка установки из корня ComfyUI:

```bash
python custom_nodes/ComfyUI-Krea2-FlowLab/verify_install.py
```

## Recommended first test for Krea-2 Turbo

Use **K2 Advanced Sampler**:

| Setting | Initial value |
|---|---:|
| steps | `8` |
| cfg | `1.0` |
| denoise | `1.0` |
| preset | `balanced` |
| schedule_profile | `native` |
| correction_strength | `0.62` |
| curvature_threshold | `0.34` |
| trust_ratio | `0.34` |
| local_trust | `0.85` |
| eta | `0.0` |

First compare with `eta=0`. Afterwards test `eta=0.15–0.30`; stochasticity is applied only in the middle of the trajectory.

### Presets

- `euler` — native Krea-2 sigma grid with plain one-call Euler updates; useful as a baseline/debug mode.
- `conservative` — closest to stable Euler behavior; smallest correction.
- `balanced` — recommended default.
- `detail` — stronger history correction; may help textures but is more experimental.

### Schedule profiles

- `native` — official-style uniformly spaced flow time followed by the model's configured shift.
- `balanced` — mild endpoint emphasis.
- `structure` — more resolution near the noisy/structural part of the trajectory.
- `detail` — more resolution near the clean/detail part.

## Modular use

Connect:

```text
MODEL ───────────────► K2 Native Scheduler ─► SIGMAS
K2 Flow Sampler ─────────────────────────────► SAMPLER
RandomNoise + CFGGuider + LATENT + both ─────► SamplerCustomAdvanced
```

The all-in-one node is simpler and produces the same sampler/scheduler internally.

## Included workflow

`examples/Full_QualityKrea2_K2FlowLab.json` is the supplied workflow with only the main sampling node replaced. The existing second pass and PiD 4× branch remain unchanged.

## Compatibility and verification

The node was written against the current ComfyUI sampler contract:

- custom sampler functions receive `(model, x, sigmas, extra_args, callback, disable)`;
- `comfy.samplers.KSAMPLER` wraps the function;
- the model returns denoised prediction and `to_d` converts it to the ODE derivative;
- Krea-2 is registered by ComfyUI as a `FLUX`/constant-flow model with shift `1.15`.

Repository tests cover:

- syntax compilation;
- node registration with a ComfyUI API-contract stub;
- creation of a valid `SAMPLER` object;
- monotonic sigma schedules and exact endpoints;
- one model call per step;
- exact integration of a constant synthetic velocity field;
- NaN/Inf and trust-region safeguards.

The self-check additionally imports the node against the user's actual ComfyUI installation.

## Troubleshooting

### Nodes do not appear

1. Confirm the folder is exactly:
   `ComfyUI/custom_nodes/ComfyUI-Krea2-FlowLab`
2. Restart ComfyUI completely.
3. Run `verify_install.py`.
4. Check the console for an earlier `IMPORT FAILED` from ComfyUI itself.

### Result is worse than the old sampler

Start with `native + conservative + eta 0`. Krea-2 Turbo is distilled for a short trajectory, so stronger correction is not universally better. Keep the original workflow for A/B testing.

### Inference time

The solver still performs one DiT call per step. Tensor-side correction normally adds only a small overhead; PiD 4× is untouched.

## License

MIT.
