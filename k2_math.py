from __future__ import annotations

import math
from dataclasses import dataclass
import torch
import torch.nn.functional as F

_EPS = 1e-8


@dataclass(frozen=True)
class SolverPreset:
    correction_strength: float
    curvature_threshold: float
    trust_ratio: float
    local_trust: float


PRESETS: dict[str, SolverPreset] = {
    "euler": SolverPreset(0.0, 0.34, 0.0, 0.0),
    "conservative": SolverPreset(0.42, 0.22, 0.22, 0.65),
    "balanced": SolverPreset(0.62, 0.34, 0.34, 0.85),
    "detail": SolverPreset(0.78, 0.48, 0.46, 1.00),
}


def batch_rms(x: torch.Tensor) -> torch.Tensor:
    dims = tuple(range(1, x.ndim))
    return x.float().square().mean(dim=dims, keepdim=True).add(_EPS).sqrt().to(x.dtype)


def batch_cosine(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    dims = tuple(range(1, a.ndim))
    af = a.float()
    bf = b.float()
    dot = (af * bf).sum(dim=dims, keepdim=True)
    den = af.square().sum(dim=dims, keepdim=True).sqrt()
    den = den * bf.square().sum(dim=dims, keepdim=True).sqrt()
    return (dot / den.clamp_min(_EPS)).clamp(-1.0, 1.0).to(a.dtype)


def curvature_confidence(
    current: torch.Tensor,
    previous: torch.Tensor,
    threshold: float,
) -> torch.Tensor:
    """Return a per-sample confidence in [0, 1] for multistep extrapolation."""
    cosine = batch_cosine(current, previous)
    angular = 0.5 * (1.0 - cosine)
    relative = batch_rms(current - previous) / batch_rms(current).clamp_min(_EPS)
    score = angular + 0.35 * relative.clamp(0.0, 2.0)
    return (1.0 - score / max(float(threshold), 1e-4)).clamp(0.0, 1.0)


def variable_ab2_delta(
    derivative: torch.Tensor,
    previous_derivative: torch.Tensor,
    step: torch.Tensor | float,
    previous_step: torch.Tensor | float,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Euler delta and variable-step Adams-Bashforth-2 correction."""
    h = torch.as_tensor(step, dtype=derivative.dtype, device=derivative.device)
    hp = torch.as_tensor(previous_step, dtype=derivative.dtype, device=derivative.device)
    ratio = (h.abs() / hp.abs().clamp_min(_EPS)).clamp(0.20, 5.0)
    euler = derivative * h
    ab2 = h * ((1.0 + 0.5 * ratio) * derivative - 0.5 * ratio * previous_derivative)
    return euler, ab2 - euler


def limit_correction(
    correction: torch.Tensor,
    euler_delta: torch.Tensor,
    trust_ratio: float,
    local_trust: float,
) -> torch.Tensor:
    """Apply global RMS and local soft trust regions to the multistep correction."""
    corr_rms = batch_rms(correction)
    euler_rms = batch_rms(euler_delta)
    scale = (float(trust_ratio) * euler_rms / corr_rms.clamp_min(_EPS)).clamp(max=1.0)
    correction = correction * scale

    if correction.ndim >= 3 and local_trust > 0:
        energy = euler_delta.float().square().mean(dim=1, keepdim=True)
        if correction.ndim == 4:
            local_scale = F.avg_pool2d(energy, kernel_size=3, stride=1, padding=1)
        elif correction.ndim == 5:
            local_scale = F.avg_pool3d(energy, kernel_size=(1, 3, 3), stride=1, padding=(0, 1, 1))
        else:
            spatial_dims = tuple(range(2, correction.ndim))
            local_scale = energy.mean(dim=spatial_dims, keepdim=True)
        local_scale = local_scale.add(_EPS).sqrt().to(correction.dtype)
        limit = (float(local_trust) * local_scale).clamp_min(1e-6)
        correction = limit * torch.tanh(correction / limit)
    return correction


def advanced_delta(
    derivative: torch.Tensor,
    previous_derivative: torch.Tensor | None,
    step: torch.Tensor | float,
    previous_step: torch.Tensor | float | None,
    *,
    correction_strength: float,
    curvature_threshold: float,
    trust_ratio: float,
    local_trust: float,
) -> torch.Tensor:
    h = torch.as_tensor(step, dtype=derivative.dtype, device=derivative.device)
    euler = derivative * h
    if previous_derivative is None or previous_step is None:
        return euler

    euler, correction = variable_ab2_delta(derivative, previous_derivative, h, previous_step)
    correction = limit_correction(correction, euler, trust_ratio, local_trust)
    confidence = curvature_confidence(derivative, previous_derivative, curvature_threshold)
    return euler + float(correction_strength) * confidence * correction


def scheduled_eta(progress: float, eta: float, start: float, end: float) -> float:
    if eta <= 0.0 or end <= start or progress <= start or progress >= end:
        return 0.0
    u = (progress - start) / (end - start)
    return float(eta) * math.sin(math.pi * u) ** 2


def warp_time_grid(u: torch.Tensor, profile: str) -> torch.Tensor:
    """Map u: 0->1 to an unshifted flow time t: 1->0."""
    if profile == "native":
        return 1.0 - u
    if profile == "structure":
        return 1.0 - u.pow(1.22)
    if profile == "detail":
        return (1.0 - u).pow(1.22)
    if profile == "balanced":
        smooth = u * u * (3.0 - 2.0 * u)
        return 1.0 - (0.65 * u + 0.35 * smooth)
    raise ValueError(f"Unknown K2 schedule profile: {profile}")


def validate_sigmas(sigmas: torch.Tensor) -> torch.Tensor:
    sigmas = torch.nan_to_num(sigmas.float(), nan=0.0, posinf=1.0, neginf=0.0)
    sigmas = sigmas.clamp(0.0, 1.0)
    if sigmas.numel() > 1:
        sigmas = torch.cummin(sigmas, dim=0).values
        sigmas[-1] = 0.0
    return sigmas
