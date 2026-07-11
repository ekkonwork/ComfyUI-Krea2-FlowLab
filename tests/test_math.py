import math
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from k2_math import (
    PRESETS,
    advanced_delta,
    scheduled_eta,
    validate_sigmas,
    variable_ab2_delta,
    warp_time_grid,
)


def test_presets_are_bounded():
    for preset in PRESETS.values():
        assert 0 <= preset.correction_strength <= 1.25
        assert preset.curvature_threshold > 0
        assert preset.trust_ratio >= 0


def test_native_grid_endpoints_and_monotonicity():
    u = torch.linspace(0, 1, 9)
    t = warp_time_grid(u, "native")
    assert t[0] == 1
    assert t[-1] == 0
    assert torch.all(t[:-1] >= t[1:])


def test_all_profiles_are_monotone():
    u = torch.linspace(0, 1, 65)
    for profile in ("native", "balanced", "structure", "detail"):
        t = warp_time_grid(u, profile)
        assert torch.isfinite(t).all()
        assert torch.all(t[:-1] >= t[1:])


def test_variable_ab2_is_exact_for_linear_derivative_on_equal_steps():
    current = torch.ones(1, 1, 1, 1)
    previous = torch.full_like(current, 2.0)
    euler, correction = variable_ab2_delta(current, previous, -1.0, -1.0)
    result = euler + correction
    assert torch.allclose(result, torch.tensor([[[[-0.5]]]]), atol=1e-6)


def test_advanced_delta_falls_back_to_euler_without_history():
    d = torch.full((2, 4, 8, 8), 2.0)
    delta = advanced_delta(
        d,
        None,
        -0.25,
        None,
        correction_strength=0.62,
        curvature_threshold=0.34,
        trust_ratio=0.34,
        local_trust=0.85,
    )
    assert torch.allclose(delta, torch.full_like(d, -0.5))


def test_scheduled_eta_is_windowed():
    assert scheduled_eta(0.0, 0.7, 0.2, 0.8) == 0
    assert scheduled_eta(1.0, 0.7, 0.2, 0.8) == 0
    mid = scheduled_eta(0.5, 0.7, 0.2, 0.8)
    assert math.isclose(mid, 0.7, rel_tol=1e-6)


def test_validate_sigmas_repairs_bad_values():
    x = torch.tensor([1.0, 0.8, float("nan"), 0.9, -1.0])
    y = validate_sigmas(x)
    assert torch.isfinite(y).all()
    assert torch.all(y[:-1] >= y[1:])
    assert y[-1] == 0


def test_variable_ab2_remains_finite_with_repeated_previous_sigma():
    current = torch.ones(1, 2, 4, 4)
    previous = torch.zeros_like(current)
    euler, correction = variable_ab2_delta(current, previous, -0.1, 0.0)
    assert torch.isfinite(euler).all()
    assert torch.isfinite(correction).all()
