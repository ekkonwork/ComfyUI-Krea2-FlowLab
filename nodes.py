from __future__ import annotations

import comfy.model_management
import comfy.sample
import comfy.samplers
import comfy.utils
import latent_preview

from .k2_math import PRESETS
from .k2_sampler import sample_k2_flow
from .k2_schedule import build_k2_sigmas

_VERSION = "0.1.1"
_CATEGORY = "sampling/custom_sampling/Krea2 FlowLab"


def make_sampler(
    preset: str,
    correction_strength: float,
    curvature_threshold: float,
    trust_ratio: float,
    local_trust: float,
    eta: float,
    eta_start: float,
    eta_end: float,
    s_noise: float,
):
    use_custom = preset == "custom"
    solver_preset = "balanced" if use_custom else preset
    return comfy.samplers.KSAMPLER(
        sample_k2_flow,
        extra_options={
            "preset": solver_preset,
            "correction_strength": correction_strength if use_custom else None,
            "curvature_threshold": curvature_threshold if use_custom else None,
            "trust_ratio": trust_ratio if use_custom else None,
            "local_trust": local_trust if use_custom else None,
            "eta": eta,
            "eta_start": eta_start,
            "eta_end": eta_end,
            "s_noise": s_noise,
        },
    )


class K2FlowSampler:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "preset": (list(PRESETS) + ["custom"], {"default": "balanced"}),
                "correction_strength": ("FLOAT", {"default": 0.62, "min": 0.0, "max": 1.25, "step": 0.01}),
                "curvature_threshold": ("FLOAT", {"default": 0.34, "min": 0.02, "max": 2.0, "step": 0.01}),
                "trust_ratio": ("FLOAT", {"default": 0.34, "min": 0.0, "max": 2.0, "step": 0.01}),
                "local_trust": ("FLOAT", {"default": 0.85, "min": 0.0, "max": 4.0, "step": 0.05}),
                "eta": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "eta_start": ("FLOAT", {"default": 0.25, "min": 0.0, "max": 1.0, "step": 0.01}),
                "eta_end": ("FLOAT", {"default": 0.72, "min": 0.0, "max": 1.0, "step": 0.01}),
                "s_noise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("SAMPLER",)
    RETURN_NAMES = ("sampler",)
    FUNCTION = "build"
    CATEGORY = _CATEGORY
    DESCRIPTION = "One-NFE-per-step Krea-2 flow sampler with variable-step AB2, curvature gating and trust-region limiting."

    def build(self, preset, correction_strength, curvature_threshold, trust_ratio, local_trust, eta, eta_start, eta_end, s_noise):
        return (make_sampler(preset, correction_strength, curvature_threshold, trust_ratio, local_trust, eta, eta_start, eta_end, s_noise),)


class K2NativeScheduler:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "steps": ("INT", {"default": 8, "min": 1, "max": 1000}),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "profile": (["native", "balanced", "structure", "detail"], {"default": "native"}),
            }
        }

    RETURN_TYPES = ("SIGMAS",)
    RETURN_NAMES = ("sigmas",)
    FUNCTION = "get_sigmas"
    CATEGORY = _CATEGORY
    DESCRIPTION = "Krea-2 native shifted flow grid; native profile reproduces the model's configured shift (1.15 for the official Turbo model)."

    def get_sigmas(self, model, steps, denoise, profile):
        return (build_k2_sigmas(model, steps, denoise, profile),)


class K2AdvancedSampler:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "latent_image": ("LATENT",),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "control_after_generate": True}),
                "steps": ("INT", {"default": 8, "min": 1, "max": 1000}),
                "cfg": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.01}),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "preset": (list(PRESETS) + ["custom"], {"default": "balanced"}),
                "schedule_profile": (["native", "balanced", "structure", "detail"], {"default": "native"}),
                "correction_strength": ("FLOAT", {"default": 0.62, "min": 0.0, "max": 1.25, "step": 0.01}),
                "curvature_threshold": ("FLOAT", {"default": 0.34, "min": 0.02, "max": 2.0, "step": 0.01}),
                "trust_ratio": ("FLOAT", {"default": 0.34, "min": 0.0, "max": 2.0, "step": 0.01}),
                "local_trust": ("FLOAT", {"default": 0.85, "min": 0.0, "max": 4.0, "step": 0.05}),
                "eta": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "eta_start": ("FLOAT", {"default": 0.25, "min": 0.0, "max": 1.0, "step": 0.01}),
                "eta_end": ("FLOAT", {"default": 0.72, "min": 0.0, "max": 1.0, "step": 0.01}),
                "s_noise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("LATENT", "LATENT", "OPTIONS")
    RETURN_NAMES = ("output", "denoised", "options")
    FUNCTION = "sample"
    CATEGORY = _CATEGORY
    DESCRIPTION = "All-in-one Krea-2 sampler. It does not modify prompts, conditioning, model weights, VAE, or downstream PiD."

    def sample(
        self,
        model,
        positive,
        negative,
        latent_image,
        seed,
        steps,
        cfg,
        denoise,
        preset,
        schedule_profile,
        correction_strength,
        curvature_threshold,
        trust_ratio,
        local_trust,
        eta,
        eta_start,
        eta_end,
        s_noise,
    ):
        latent = latent_image.copy()
        latent_samples = comfy.sample.fix_empty_latent_channels(
            model,
            latent["samples"],
            latent.get("downscale_ratio_spacial"),
            latent.get("downscale_ratio_temporal"),
        )
        latent["samples"] = latent_samples

        sigmas = build_k2_sigmas(model, steps, denoise, schedule_profile)
        if sigmas.numel() == 0:
            options = {"sampler_name": "k2_flow", "scheduler": f"k2_{schedule_profile}"}
            return (latent, latent, options)

        noise = comfy.sample.prepare_noise(latent_samples, seed, latent.get("batch_index"))
        sampler = make_sampler(
            preset,
            correction_strength,
            curvature_threshold,
            trust_ratio,
            local_trust,
            eta,
            eta_start,
            eta_end,
            s_noise,
        )

        x0_output = {}
        callback = latent_preview.prepare_callback(model, sigmas.shape[-1] - 1, x0_output)
        samples = comfy.sample.sample_custom(
            model,
            noise,
            cfg,
            sampler,
            sigmas,
            positive,
            negative,
            latent_samples,
            noise_mask=latent.get("noise_mask"),
            callback=callback,
            disable_pbar=not comfy.utils.PROGRESS_BAR_ENABLED,
            seed=seed,
        )

        out = latent.copy()
        out.pop("downscale_ratio_spacial", None)
        out.pop("downscale_ratio_temporal", None)
        out["samples"] = samples

        if "x0" in x0_output:
            x0 = model.model.process_latent_out(x0_output["x0"].cpu())
            denoised_out = latent.copy()
            denoised_out.pop("downscale_ratio_spacial", None)
            denoised_out.pop("downscale_ratio_temporal", None)
            denoised_out["samples"] = x0
        else:
            denoised_out = out

        options = {
            "sampler_name": f"k2_flow/{preset}",
            "scheduler": f"k2_{schedule_profile}",
            "steps": int(steps),
            "eta": float(eta),
            "version": _VERSION,
        }
        return (out, denoised_out, options)


NODE_CLASS_MAPPINGS = {
    "K2FlowSampler": K2FlowSampler,
    "K2NativeScheduler": K2NativeScheduler,
    "K2AdvancedSampler": K2AdvancedSampler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "K2FlowSampler": "K2 Flow Sampler",
    "K2NativeScheduler": "K2 Native Scheduler",
    "K2AdvancedSampler": "K2 Advanced Sampler",
}
