from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    comfy_root = root.parent.parent
    sys.path.insert(0, str(comfy_root))
    sys.path.insert(0, str(root.parent))

    # ComfyUI parses an empty argument list during library-style imports unless
    # argument parsing is explicitly enabled. Enable its official parser before
    # selecting CPU mode on CPU-only CI runners. GPU installations are untouched.
    try:
        import torch
        import comfy.options
        if not torch.cuda.is_available():
            comfy.options.enable_args_parsing(True)
            if "--cpu" not in sys.argv:
                sys.argv.append("--cpu")
    except Exception:
        pass

    try:
        import comfy.samplers  # noqa: F401
        import comfy.sample  # noqa: F401
        import latent_preview  # noqa: F401
    except Exception as exc:
        print(f"FAIL: ComfyUI imports are unavailable: {exc}")
        print("Run this command from a normal ComfyUI installation after cloning into custom_nodes.")
        return 1

    module_name = root.name.replace("-", "_")
    spec = importlib.util.spec_from_file_location(
        module_name,
        root / "__init__.py",
        submodule_search_locations=[str(root)],
    )
    if spec is None or spec.loader is None:
        print("FAIL: could not create module spec")
        return 1
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    expected = {"K2FlowSampler", "K2NativeScheduler", "K2AdvancedSampler"}
    found = set(module.NODE_CLASS_MAPPINGS)
    if not expected.issubset(found):
        print(f"FAIL: missing nodes: {sorted(expected - found)}")
        return 1

    sampler_node = module.NODE_CLASS_MAPPINGS["K2FlowSampler"]()
    sampler = sampler_node.build("balanced", 0.62, 0.34, 0.34, 0.85, 0.0, 0.25, 0.72, 1.0)[0]
    if not hasattr(sampler, "sample"):
        print("FAIL: ComfyUI did not create a valid SAMPLER object")
        return 1

    print("OK: ComfyUI imports succeeded")
    print("OK: all three nodes are registered")
    print("OK: K2 Flow Sampler produces a ComfyUI SAMPLER object")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
