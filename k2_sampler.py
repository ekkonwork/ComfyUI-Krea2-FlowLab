from __future__ import annotations

import torch

from .k2_math import PRESETS, advanced_delta, scheduled_eta


def _model_sampling_from_wrapper(model):
    try:
        return model.inner_model.model_patcher.get_model_object("model_sampling")
    except Exception:
        try:
            return model.inner_model.inner_model.model_sampling
        except Exception:
            return None


@torch.no_grad()
def sample_k2_flow(
    model,
    x: torch.Tensor,
    sigmas: torch.Tensor,
    extra_args=None,
    callback=None,
    disable=None,
    *,
    preset: str = "balanced",
    correction_strength: float | None = None,
    curvature_threshold: float | None = None,
    trust_ratio: float | None = None,
    local_trust: float | None = None,
    eta: float = 0.0,
    eta_start: float = 0.25,
    eta_end: float = 0.72,
    s_noise: float = 1.0,
    noise_sampler=None,
):
    """Krea-2/flow-oriented one-evaluation-per-step sampler.

    The deterministic path uses variable-step AB2, curvature-aware blending and
    trust-region limiting. Optional stochasticity follows ComfyUI's rectified-
    flow ancestral transport but is windowed to the middle of the trajectory.
    """
    from comfy.k_diffusion.sampling import default_noise_sampler, to_d
    from comfy.utils import model_trange

    extra_args = {} if extra_args is None else extra_args
    if preset not in PRESETS:
        raise ValueError(f"Unknown K2 solver preset: {preset}")
    base = PRESETS[preset]
    correction_strength = base.correction_strength if correction_strength is None else correction_strength
    curvature_threshold = base.curvature_threshold if curvature_threshold is None else curvature_threshold
    trust_ratio = base.trust_ratio if trust_ratio is None else trust_ratio
    local_trust = base.local_trust if local_trust is None else local_trust

    seed = extra_args.get("seed")
    noise_sampler = default_noise_sampler(x, seed=seed) if noise_sampler is None else noise_sampler
    model_sampling = _model_sampling_from_wrapper(model)
    noise_scale = float(getattr(model_sampling, "noise_scale", 1.0)) if model_sampling is not None else 1.0
    s_in = x.new_ones([x.shape[0]])

    previous_d = None
    previous_h = None
    total = max(len(sigmas) - 1, 1)

    for i in model_trange(len(sigmas) - 1, disable=disable):
        sigma = sigmas[i]
        sigma_next = sigmas[i + 1]
        denoised = model(x, sigma * s_in, **extra_args)
        denoised = torch.nan_to_num(denoised, nan=0.0, posinf=0.0, neginf=0.0)
        d = to_d(x, sigma, denoised)
        d = torch.nan_to_num(d, nan=0.0, posinf=0.0, neginf=0.0)

        if callback is not None:
            callback({"x": x, "i": i, "sigma": sigma, "sigma_hat": sigma, "denoised": denoised})

        if float(sigma_next) == 0.0:
            x = denoised
            break

        progress = i / max(total - 1, 1)
        eta_i = scheduled_eta(progress, float(eta), float(eta_start), float(eta_end))

        sigma_down = sigma_next
        if eta_i > 0.0:
            ratio = sigma_next / sigma
            sigma_down = sigma_next * (1.0 + (ratio - 1.0) * eta_i)

        h = sigma_down - sigma
        delta = advanced_delta(
            d,
            previous_d,
            h,
            previous_h,
            correction_strength=float(correction_strength),
            curvature_threshold=float(curvature_threshold),
            trust_ratio=float(trust_ratio),
            local_trust=float(local_trust),
        )
        x = x + delta

        if eta_i > 0.0:
            alpha_next = 1.0 - sigma_next
            alpha_down = 1.0 - sigma_down
            radicand = sigma_next.square() - sigma_down.square() * alpha_next.square() / alpha_down.square().clamp_min(1e-8)
            renoise_coeff = radicand.clamp_min(0.0).sqrt()
            x = (alpha_next / alpha_down.clamp_min(1e-8)) * x
            x = x + noise_sampler(sigma, sigma_next) * (float(s_noise) * noise_scale) * renoise_coeff

        x = torch.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
        previous_d = d
        previous_h = h

    return x
