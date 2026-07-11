from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "k2flowlab_testpkg"


def install_comfy_stubs():
    comfy = types.ModuleType("comfy")
    samplers = types.ModuleType("comfy.samplers")
    sample = types.ModuleType("comfy.sample")
    utils = types.ModuleType("comfy.utils")
    model_management = types.ModuleType("comfy.model_management")
    kd = types.ModuleType("comfy.k_diffusion")
    kd_sampling = types.ModuleType("comfy.k_diffusion.sampling")
    latent_preview = types.ModuleType("latent_preview")

    class KSAMPLER:
        def __init__(self, fn, extra_options=None, inpaint_options=None):
            self.sampler_function = fn
            self.extra_options = extra_options or {}

        def sample(self, *args, **kwargs):
            return self.sampler_function(*args, **self.extra_options, **kwargs)

    samplers.KSAMPLER = KSAMPLER
    utils.PROGRESS_BAR_ENABLED = False
    utils.model_trange = lambda n, disable=None: range(n)

    def to_d(x, sigma, denoised):
        shape = (sigma.shape[0],) + (1,) * (x.ndim - 1) if sigma.ndim else (1,) * x.ndim
        return (x - denoised) / sigma.reshape(shape)

    kd_sampling.to_d = to_d
    kd_sampling.default_noise_sampler = lambda x, seed=None: (lambda a, b: torch.zeros_like(x))
    latent_preview.prepare_callback = lambda *args, **kwargs: None

    comfy.samplers = samplers
    comfy.sample = sample
    comfy.utils = utils
    comfy.model_management = model_management
    comfy.k_diffusion = kd
    kd.sampling = kd_sampling

    sys.modules.update({
        "comfy": comfy,
        "comfy.samplers": samplers,
        "comfy.sample": sample,
        "comfy.utils": utils,
        "comfy.model_management": model_management,
        "comfy.k_diffusion": kd,
        "comfy.k_diffusion.sampling": kd_sampling,
        "latent_preview": latent_preview,
    })


def load_package():
    install_comfy_stubs()
    for name in list(sys.modules):
        if name == PACKAGE_NAME or name.startswith(PACKAGE_NAME + "."):
            del sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME,
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = module
    spec.loader.exec_module(module)
    return module


def test_package_import_and_node_registration():
    pkg = load_package()
    assert {"K2FlowSampler", "K2NativeScheduler", "K2AdvancedSampler"}.issubset(pkg.NODE_CLASS_MAPPINGS)
    sampler = pkg.NODE_CLASS_MAPPINGS["K2FlowSampler"]().build(
        "balanced", 0.62, 0.34, 0.34, 0.85, 0.0, 0.25, 0.72, 1.0
    )[0]
    assert hasattr(sampler, "sample")


def test_sampler_uses_one_model_call_per_step_and_integrates_constant_field():
    load_package()
    sampler_mod = sys.modules[f"{PACKAGE_NAME}.k2_sampler"]

    class MockModel:
        def __init__(self):
            self.calls = 0

        def __call__(self, x, sigma, **kwargs):
            self.calls += 1
            shape = (sigma.shape[0],) + (1,) * (x.ndim - 1)
            return x - sigma.reshape(shape) * 2.0

    model = MockModel()
    x = torch.zeros(1, 4, 8, 8)
    sigmas = torch.tensor([1.0, 0.75, 0.5, 0.25, 0.0])
    out = sampler_mod.sample_k2_flow(model, x, sigmas, preset="balanced")
    assert model.calls == len(sigmas) - 1
    assert torch.allclose(out, torch.full_like(out, -2.0), atol=1e-5)


def test_stochastic_path_is_finite_and_keeps_one_call_per_step():
    load_package()
    sampler_mod = sys.modules[f"{PACKAGE_NAME}.k2_sampler"]

    class MockSampling:
        noise_scale = 1.0

    class Patcher:
        def get_model_object(self, name):
            assert name == "model_sampling"
            return MockSampling()

    class Inner:
        model_patcher = Patcher()

    class WrappedModel:
        inner_model = Inner()

        def __init__(self):
            self.calls = 0

        def __call__(self, x, sigma, **kwargs):
            self.calls += 1
            shape = (sigma.shape[0],) + (1,) * (x.ndim - 1)
            return x - sigma.reshape(shape) * torch.tanh(x + 0.25)

    model = WrappedModel()
    x = torch.randn(1, 4, 16, 16)
    sigmas = torch.tensor([1.0, 0.82, 0.61, 0.39, 0.18, 0.0])
    out = sampler_mod.sample_k2_flow(
        model,
        x,
        sigmas,
        extra_args={"seed": 123},
        preset="balanced",
        eta=0.25,
        eta_start=0.1,
        eta_end=0.9,
    )
    assert model.calls == len(sigmas) - 1
    assert torch.isfinite(out).all()


def test_named_presets_are_not_overridden_by_visible_custom_widgets():
    pkg = load_package()
    node = pkg.NODE_CLASS_MAPPINGS["K2FlowSampler"]()
    euler = node.build("euler", 0.99, 0.99, 0.99, 0.99, 0.0, 0.25, 0.72, 1.0)[0]
    assert euler.extra_options["preset"] == "euler"
    assert euler.extra_options["correction_strength"] is None
    custom = node.build("custom", 0.73, 0.41, 0.29, 0.91, 0.0, 0.25, 0.72, 1.0)[0]
    assert custom.extra_options["preset"] == "balanced"
    assert custom.extra_options["correction_strength"] == 0.73
