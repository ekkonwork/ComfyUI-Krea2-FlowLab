from __future__ import annotations

from dataclasses import asdict, dataclass


MANUAL_PROFILE = "00 Manual widgets"
MY_BEST_PROFILE = "01 MY BEST - balanced native eta 0.35"


@dataclass(frozen=True)
class K2FullProfile:
    preset: str
    schedule_profile: str
    correction_strength: float
    curvature_threshold: float
    trust_ratio: float
    local_trust: float
    eta: float
    eta_start: float
    eta_end: float
    s_noise: float
    tier: str
    description: str

    def to_dict(self) -> dict:
        return asdict(self)


def _profile(
    schedule_profile: str,
    correction_strength: float,
    curvature_threshold: float,
    trust_ratio: float,
    local_trust: float,
    eta: float,
    eta_start: float,
    eta_end: float,
    s_noise: float,
    tier: str,
    description: str,
) -> K2FullProfile:
    # Full profiles always use the explicit/custom path so every displayed
    # number below is applied exactly instead of being replaced by a solver preset.
    return K2FullProfile(
        preset="custom",
        schedule_profile=schedule_profile,
        correction_strength=correction_strength,
        curvature_threshold=curvature_threshold,
        trust_ratio=trust_ratio,
        local_trust=local_trust,
        eta=eta,
        eta_start=eta_start,
        eta_end=eta_end,
        s_noise=s_noise,
        tier=tier,
        description=description,
    )


FULL_PROFILES: dict[str, K2FullProfile] = {
    MY_BEST_PROFILE: _profile(
        "native", 0.62, 0.34, 0.34, 0.85, 0.35, 0.25, 0.72, 1.00,
        "recommended",
        "The exact user-validated winner: balanced solver values, native grid and eta 0.35.",
    ),
    "02 REFERENCE - Euler deterministic": _profile(
        "native", 0.00, 0.34, 0.00, 0.00, 0.00, 0.25, 0.72, 1.00,
        "reference",
        "Plain one-call Euler on the native grid; useful as a neutral baseline.",
    ),
    "03 SAFE - clean conservative": _profile(
        "native", 0.42, 0.22, 0.22, 0.65, 0.10, 0.30, 0.62, 0.85,
        "safe",
        "Low correction and a narrow, weak noise window for clean stable outputs.",
    ),
    "04 SAFE - portrait": _profile(
        "native", 0.50, 0.26, 0.24, 0.70, 0.18, 0.32, 0.64, 0.90,
        "safe",
        "Conservative local motion intended to reduce facial and anatomical instability.",
    ),
    "05 SAFE - architecture geometry": _profile(
        "structure", 0.48, 0.25, 0.22, 0.65, 0.05, 0.35, 0.58, 0.80,
        "safe",
        "Structure-weighted schedule with very little stochasticity for straight geometry.",
    ),
    "06 NORMAL - product crisp": _profile(
        "detail", 0.58, 0.32, 0.28, 0.75, 0.12, 0.35, 0.68, 0.85,
        "normal",
        "Controlled late-step emphasis for materials, edges and product-style images.",
    ),
    "07 NORMAL - balanced deterministic": _profile(
        "native", 0.62, 0.34, 0.34, 0.85, 0.00, 0.25, 0.72, 1.00,
        "normal",
        "Balanced solver on the native grid with no re-noising.",
    ),
    "08 NORMAL - balanced soft": _profile(
        "native", 0.58, 0.32, 0.30, 0.78, 0.22, 0.30, 0.68, 0.92,
        "normal",
        "Slightly softer and safer than the recommended profile.",
    ),
    "09 NORMAL - balanced rich": _profile(
        "native", 0.66, 0.38, 0.38, 0.92, 0.40, 0.20, 0.78, 1.05,
        "normal",
        "More correction and texture variation while staying near the native trajectory.",
    ),
    "10 NORMAL - structure first": _profile(
        "structure", 0.62, 0.34, 0.32, 0.82, 0.20, 0.28, 0.66, 0.92,
        "normal",
        "Spends more schedule resolution while composition and large forms are established.",
    ),
    "11 NORMAL - detail first": _profile(
        "detail", 0.64, 0.38, 0.36, 0.90, 0.24, 0.28, 0.74, 0.95,
        "normal",
        "Allocates more schedule resolution near the clean/detail end of the trajectory.",
    ),
    "12 CREATIVE - cinematic": _profile(
        "balanced", 0.64, 0.38, 0.38, 0.92, 0.36, 0.18, 0.80, 1.02,
        "creative",
        "Broad but moderate stochastic window for richer lighting and cinematic variation.",
    ),
    "13 CREATIVE - organic texture": _profile(
        "detail", 0.68, 0.42, 0.40, 1.00, 0.45, 0.15, 0.84, 1.08,
        "creative",
        "Texture-forward profile for foliage, hair, fabric and other organic detail.",
    ),
    "14 EXPERIMENTAL - smooth low trust": _profile(
        "native", 0.56, 0.30, 0.20, 0.58, 0.25, 0.28, 0.68, 0.95,
        "experimental",
        "Allows prediction but clamps its global and local size strongly.",
    ),
    "15 EXPERIMENTAL - high trust": _profile(
        "native", 0.70, 0.44, 0.52, 1.15, 0.30, 0.22, 0.76, 1.00,
        "experimental",
        "Lets the multistep estimate influence the path more strongly; watch for overshoot.",
    ),
    "16 EXPERIMENTAL - late detail noise": _profile(
        "detail", 0.62, 0.34, 0.34, 0.85, 0.42, 0.42, 0.86, 0.95,
        "experimental",
        "Keeps structure deterministic, then injects variation later for fine detail.",
    ),
    "17 EXPERIMENTAL - early creative structure": _profile(
        "structure", 0.66, 0.40, 0.38, 0.92, 0.40, 0.08, 0.58, 1.00,
        "experimental",
        "Introduces stochasticity early enough to alter layout and large visual ideas.",
    ),
    "18 EXPERIMENTAL - wide eta window": _profile(
        "native", 0.64, 0.38, 0.36, 0.90, 0.38, 0.08, 0.90, 0.95,
        "experimental",
        "Long stochastic window with restrained noise amplitude.",
    ),
    "19 EXTREME - detail": _profile(
        "detail", 0.88, 0.62, 0.65, 1.40, 0.50, 0.12, 0.88, 1.15,
        "extreme",
        "Aggressive correction and detail emphasis; can create striking or false texture.",
    ),
    "20 EXTREME - creative": _profile(
        "balanced", 0.82, 0.58, 0.60, 1.30, 0.72, 0.05, 0.94, 1.30,
        "extreme",
        "High stochasticity and high solver freedom for unusual compositions and textures.",
    ),
    "21 EXTREME - chaos": _profile(
        "detail", 1.10, 0.90, 0.95, 2.00, 0.95, 0.02, 0.98, 1.60,
        "extreme",
        "Stress-test profile near the exposed limits; artifacts and instability are expected.",
    ),
}

PROFILE_CHOICES = [MANUAL_PROFILE, *FULL_PROFILES.keys()]


def resolve_full_profile(
    name: str,
    *,
    preset: str,
    schedule_profile: str,
    correction_strength: float,
    curvature_threshold: float,
    trust_ratio: float,
    local_trust: float,
    eta: float,
    eta_start: float,
    eta_end: float,
    s_noise: float,
) -> K2FullProfile:
    if name == MANUAL_PROFILE:
        return K2FullProfile(
            preset=preset,
            schedule_profile=schedule_profile,
            correction_strength=float(correction_strength),
            curvature_threshold=float(curvature_threshold),
            trust_ratio=float(trust_ratio),
            local_trust=float(local_trust),
            eta=float(eta),
            eta_start=float(eta_start),
            eta_end=float(eta_end),
            s_noise=float(s_noise),
            tier="manual",
            description="Use the visible sampler widgets without profile overrides.",
        )
    try:
        return FULL_PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown K2 full profile: {name}") from exc
