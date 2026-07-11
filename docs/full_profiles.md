# K2 Advanced Sampler full profiles

`full_profile` is an all-in-one selector appended to **K2 Advanced Sampler**. `00 Manual widgets` preserves the traditional behavior and uses every visible widget. Any other selection overrides `preset`, `schedule_profile`, the four solver controls, `eta`, the eta window, and `s_noise` internally.

The saved winner is **`01 MY BEST - balanced native eta 0.35`**. It reproduces exactly: balanced solver values (`0.62 / 0.34 / 0.34 / 0.85`), native schedule, `eta=0.35`, `eta_start=0.25`, `eta_end=0.72`, and `s_noise=1.0`.

Extreme profiles are deliberate stress tests. They may produce false texture, broken geometry, overshoot, or unstable results; keep the recommended profile for production and compare with fixed seeds.

| Profile | Tier | Schedule | Correction | Curvature | Trust | Local trust | Eta | Eta start | Eta end | S-noise | Intent |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `01 MY BEST - balanced native eta 0.35` | `recommended` | `native` | `0.62` | `0.34` | `0.34` | `0.85` | `0.35` | `0.25` | `0.72` | `1.00` | The exact user-validated winner: balanced solver values, native grid and eta 0.35. |
| `02 REFERENCE - Euler deterministic` | `reference` | `native` | `0.00` | `0.34` | `0.00` | `0.00` | `0.00` | `0.25` | `0.72` | `1.00` | Plain one-call Euler on the native grid; useful as a neutral baseline. |
| `03 SAFE - clean conservative` | `safe` | `native` | `0.42` | `0.22` | `0.22` | `0.65` | `0.10` | `0.30` | `0.62` | `0.85` | Low correction and a narrow, weak noise window for clean stable outputs. |
| `04 SAFE - portrait` | `safe` | `native` | `0.50` | `0.26` | `0.24` | `0.70` | `0.18` | `0.32` | `0.64` | `0.90` | Conservative local motion intended to reduce facial and anatomical instability. |
| `05 SAFE - architecture geometry` | `safe` | `structure` | `0.48` | `0.25` | `0.22` | `0.65` | `0.05` | `0.35` | `0.58` | `0.80` | Structure-weighted schedule with very little stochasticity for straight geometry. |
| `06 NORMAL - product crisp` | `normal` | `detail` | `0.58` | `0.32` | `0.28` | `0.75` | `0.12` | `0.35` | `0.68` | `0.85` | Controlled late-step emphasis for materials, edges and product-style images. |
| `07 NORMAL - balanced deterministic` | `normal` | `native` | `0.62` | `0.34` | `0.34` | `0.85` | `0.00` | `0.25` | `0.72` | `1.00` | Balanced solver on the native grid with no re-noising. |
| `08 NORMAL - balanced soft` | `normal` | `native` | `0.58` | `0.32` | `0.30` | `0.78` | `0.22` | `0.30` | `0.68` | `0.92` | Slightly softer and safer than the recommended profile. |
| `09 NORMAL - balanced rich` | `normal` | `native` | `0.66` | `0.38` | `0.38` | `0.92` | `0.40` | `0.20` | `0.78` | `1.05` | More correction and texture variation while staying near the native trajectory. |
| `10 NORMAL - structure first` | `normal` | `structure` | `0.62` | `0.34` | `0.32` | `0.82` | `0.20` | `0.28` | `0.66` | `0.92` | Spends more schedule resolution while composition and large forms are established. |
| `11 NORMAL - detail first` | `normal` | `detail` | `0.64` | `0.38` | `0.36` | `0.90` | `0.24` | `0.28` | `0.74` | `0.95` | Allocates more schedule resolution near the clean/detail end of the trajectory. |
| `12 CREATIVE - cinematic` | `creative` | `balanced` | `0.64` | `0.38` | `0.38` | `0.92` | `0.36` | `0.18` | `0.80` | `1.02` | Broad but moderate stochastic window for richer lighting and cinematic variation. |
| `13 CREATIVE - organic texture` | `creative` | `detail` | `0.68` | `0.42` | `0.40` | `1.00` | `0.45` | `0.15` | `0.84` | `1.08` | Texture-forward profile for foliage, hair, fabric and other organic detail. |
| `14 EXPERIMENTAL - smooth low trust` | `experimental` | `native` | `0.56` | `0.30` | `0.20` | `0.58` | `0.25` | `0.28` | `0.68` | `0.95` | Allows prediction but clamps its global and local size strongly. |
| `15 EXPERIMENTAL - high trust` | `experimental` | `native` | `0.70` | `0.44` | `0.52` | `1.15` | `0.30` | `0.22` | `0.76` | `1.00` | Lets the multistep estimate influence the path more strongly; watch for overshoot. |
| `16 EXPERIMENTAL - late detail noise` | `experimental` | `detail` | `0.62` | `0.34` | `0.34` | `0.85` | `0.42` | `0.42` | `0.86` | `0.95` | Keeps structure deterministic, then injects variation later for fine detail. |
| `17 EXPERIMENTAL - early creative structure` | `experimental` | `structure` | `0.66` | `0.40` | `0.38` | `0.92` | `0.40` | `0.08` | `0.58` | `1.00` | Introduces stochasticity early enough to alter layout and large visual ideas. |
| `18 EXPERIMENTAL - wide eta window` | `experimental` | `native` | `0.64` | `0.38` | `0.36` | `0.90` | `0.38` | `0.08` | `0.90` | `0.95` | Long stochastic window with restrained noise amplitude. |
| `19 EXTREME - detail` | `extreme` | `detail` | `0.88` | `0.62` | `0.65` | `1.40` | `0.50` | `0.12` | `0.88` | `1.15` | Aggressive correction and detail emphasis; can create striking or false texture. |
| `20 EXTREME - creative` | `extreme` | `balanced` | `0.82` | `0.58` | `0.60` | `1.30` | `0.72` | `0.05` | `0.94` | `1.30` | High stochasticity and high solver freedom for unusual compositions and textures. |
| `21 EXTREME - chaos` | `extreme` | `detail` | `1.10` | `0.90` | `0.95` | `2.00` | `0.95` | `0.02` | `0.98` | `1.60` | Stress-test profile near the exposed limits; artifacts and instability are expected. |

## Recommended use

1. Keep the same prompt, model, latent, seed, resolution, CFG and steps.
2. Compare `01 MY BEST` against one candidate profile at a time.
3. Judge raw decoded images before PiD/upscaling.
4. Use at least 10–20 fixed seeds before promoting a profile to production.

## Backward compatibility

Existing workflows continue to use `00 Manual widgets` by default. The new selector is appended as an optional widget, so old saved widget positions are not shifted.
