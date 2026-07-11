from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("k2_profiles", ROOT / "profiles.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def manual_values():
    return {
        "preset": "balanced",
        "schedule_profile": "native",
        "correction_strength": 0.62,
        "curvature_threshold": 0.34,
        "trust_ratio": 0.34,
        "local_trust": 0.85,
        "eta": 0.35,
        "eta_start": 0.25,
        "eta_end": 0.72,
        "s_noise": 1.0,
    }


def test_profile_count_and_order():
    assert MODULE.PROFILE_CHOICES[0] == MODULE.MANUAL_PROFILE
    assert MODULE.PROFILE_CHOICES[1] == MODULE.MY_BEST_PROFILE
    assert len(MODULE.FULL_PROFILES) == 21  # saved winner + 20 additional profiles


def test_my_best_profile_is_exactly_preserved():
    profile = MODULE.FULL_PROFILES[MODULE.MY_BEST_PROFILE]
    assert profile.preset == "custom"
    assert profile.schedule_profile == "native"
    assert profile.correction_strength == 0.62
    assert profile.curvature_threshold == 0.34
    assert profile.trust_ratio == 0.34
    assert profile.local_trust == 0.85
    assert profile.eta == 0.35
    assert profile.eta_start == 0.25
    assert profile.eta_end == 0.72
    assert profile.s_noise == 1.0


def test_manual_profile_preserves_visible_widgets():
    values = manual_values()
    resolved = MODULE.resolve_full_profile(MODULE.MANUAL_PROFILE, **values)
    for key, value in values.items():
        assert getattr(resolved, key) == value


def test_all_profiles_are_inside_node_ranges():
    schedules = {"native", "balanced", "structure", "detail"}
    for name, profile in MODULE.FULL_PROFILES.items():
        assert profile.preset == "custom", name
        assert profile.schedule_profile in schedules, name
        assert 0.0 <= profile.correction_strength <= 1.25, name
        assert 0.02 <= profile.curvature_threshold <= 2.0, name
        assert 0.0 <= profile.trust_ratio <= 2.0, name
        assert 0.0 <= profile.local_trust <= 4.0, name
        assert 0.0 <= profile.eta <= 1.0, name
        assert 0.0 <= profile.eta_start < profile.eta_end <= 1.0, name
        assert 0.0 <= profile.s_noise <= 2.0, name


def test_unknown_profile_fails_closed():
    try:
        MODULE.resolve_full_profile("does not exist", **manual_values())
    except ValueError as exc:
        assert "Unknown K2 full profile" in str(exc)
    else:
        raise AssertionError("unknown profile was silently accepted")
