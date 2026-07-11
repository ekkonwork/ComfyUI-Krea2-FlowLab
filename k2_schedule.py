from __future__ import annotations

import torch

from .k2_math import validate_sigmas, warp_time_grid


def build_k2_sigmas(model, steps: int, denoise: float = 1.0, profile: str = "native") -> torch.Tensor:
    if steps < 1:
        raise ValueError("steps must be at least 1")
    if denoise <= 0.0:
        return torch.empty(0, dtype=torch.float32)

    total_steps = steps if denoise >= 1.0 else max(steps, int(steps / denoise))
    u = torch.linspace(0.0, 1.0, total_steps + 1, dtype=torch.float32)
    t = warp_time_grid(u, profile)

    model_sampling = model.get_model_object("model_sampling")
    class_name = model_sampling.__class__.__name__
    if "DiscreteFlow" in class_name:
        t_model = t * float(getattr(model_sampling, "multiplier", 1000.0))
    else:
        t_model = t

    sigmas = model_sampling.sigma(t_model)
    sigmas = validate_sigmas(sigmas.detach().cpu())
    sigmas[0] = min(float(sigmas[0]), 1.0)
    sigmas[-1] = 0.0

    if total_steps != steps:
        sigmas = sigmas[-(steps + 1):]
    return sigmas
