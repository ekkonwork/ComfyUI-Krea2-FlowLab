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
[K2 FlowLab] v0.1.1 loaded: K2 Advanced Sampler, K2 Flow Sampler, K2 Native Scheduler
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
5. Для первого теста используй `balanced + native + eta 0`. Для контрольного результата без multistep-коррекции выбери `euler`.

Проверка установки из корня ComfyUI:

```bash
python custom_nodes/ComfyUI-Krea2-FlowLab/verify_install.py
```

## Patch the supplied Full_QualityKrea2 workflow

The repository includes a guarded patcher rather than embedding a large user workflow in git history. It only replaces the supported main sampler node and preserves the prompt/conditioning path, the second refine pass, and the core PiD 4× branch.

From the repository folder:

```bash
python tools/patch_workflow.py /path/to/Full_QualityKrea2.json
```

It writes:

```text
Full_QualityKrea2_K2FlowLab.json
```

You can also provide an explicit output path:

```bash
python tools/patch_workflow.py input.json output.json
```

The script refuses to modify a workflow if the expected subgraph or sampler node is missing or has an unexpected type.

## Recommended first test for Krea-2 Turbo

Use **K2 Advanced Sampler**:

| Setting | Initial value |
|---|---:|
| steps | `8` |
| cfg | `1.0` |
| denoise | `1.0` |
| preset | `balanced` |
| schedule_profile | `native` |
| correction_strength | ignored unless preset=`custom` |
| curvature_threshold | ignored unless preset=`custom` |
| trust_ratio | ignored unless preset=`custom` |
| local_trust | ignored unless preset=`custom` |
| eta | `0.0` |

First compare with `eta=0`. Afterwards test `eta=0.15–0.30`; stochasticity is applied only in the middle of the trajectory.

### Presets

- `euler` — native Krea-2 sigma grid with plain one-call Euler updates; useful as a baseline/debug mode.
- `conservative` — closest to stable Euler behavior; smallest correction.
- `balanced` — recommended default.
- `detail` — stronger history correction; may help textures but is more experimental.
- `custom` — uses the four manual correction/trust widgets.

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

## Compatibility and verification

The node follows the current ComfyUI sampler contract:

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
- NaN/Inf and trust-region safeguards;
- named preset behavior;
- guarded workflow rewiring while preserving PiD settings.

GitHub Actions also clones the current official ComfyUI, installs the repository exactly under `custom_nodes`, and runs `verify_install.py`.

## Troubleshooting

### Nodes do not appear

1. Confirm the folder is exactly `ComfyUI/custom_nodes/ComfyUI-Krea2-FlowLab`.
2. Restart ComfyUI completely.
3. Run `verify_install.py`.
4. Check the console for an earlier `IMPORT FAILED` from ComfyUI itself.

### Result is worse than the old sampler

Start with `native + conservative + eta 0`. Krea-2 Turbo is distilled for a short trajectory, so stronger correction is not universally better. Keep the original workflow for A/B testing.

### Inference time

The solver still performs one DiT call per step. Tensor-side correction normally adds only a small overhead; PiD 4× is untouched.

## License

MIT.
