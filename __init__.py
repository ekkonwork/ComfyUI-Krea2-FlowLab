"""ComfyUI entrypoint for K2 FlowLab."""

# Pytest imports repository-level ``__init__.py`` as a standalone module when
# the checkout directory contains dashes. ComfyUI imports it as a package, so
# only register nodes in the real package-import path.
if __package__:
    from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

    print("[K2 FlowLab] v0.2.0 loaded: K2 Advanced Sampler, K2 Flow Sampler, K2 Native Scheduler, 21 full profiles")
else:  # pragma: no cover - tooling-only fallback
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
