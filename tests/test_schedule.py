from __future__ import annotations

import importlib
import math
import sys
import types
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "k2flowlab_schedule_pkg"
pkg = types.ModuleType(PACKAGE)
pkg.__path__ = [str(ROOT)]
sys.modules[PACKAGE] = pkg
build_k2_sigmas = importlib.import_module(f"{PACKAGE}.k2_schedule").build_k2_sigmas


class FakeFluxSampling:
    shift = 1.15

    def sigma(self, timestep):
        t = timestep.float()
        alpha = math.exp(self.shift)
        safe = t.clamp(1e-8, 1.0)
        out = alpha / (alpha + (1.0 / safe - 1.0))
        return torch.where(t <= 0, torch.zeros_like(out), out)


class FakeModel:
    def __init__(self):
        self.sampling = FakeFluxSampling()

    def get_model_object(self, name):
        assert name == "model_sampling"
        return self.sampling


def test_native_scheduler_matches_shifted_uniform_krea_grid():
    model = FakeModel()
    sigmas = build_k2_sigmas(model, 8, 1.0, "native")
    t = torch.linspace(1.0, 0.0, 9)
    expected = model.sampling.sigma(t)
    expected[-1] = 0.0
    assert torch.allclose(sigmas, expected, atol=1e-7)
    assert sigmas[0] == 1.0
    assert sigmas[-1] == 0.0


def test_partial_denoise_returns_tail_with_requested_step_count():
    sigmas = build_k2_sigmas(FakeModel(), 4, 0.5, "native")
    assert len(sigmas) == 5
    assert 0.0 < float(sigmas[0]) < 1.0
    assert sigmas[-1] == 0.0
