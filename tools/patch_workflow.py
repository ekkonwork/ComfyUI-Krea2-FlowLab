from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

MAIN_SUBGRAPH_ID = "cff27ed2-98c9-40c2-96d6-684cb6a56ffd"
MAIN_NODE_ID = 116


def patch_workflow(data: dict) -> dict:
    out = copy.deepcopy(data)
    subgraphs = out.get("definitions", {}).get("subgraphs", [])
    graph = next((g for g in subgraphs if g.get("id") == MAIN_SUBGRAPH_ID), None)
    if graph is None:
        raise ValueError("Main sampler subgraph was not found; workflow layout is different from the supported Full_QualityKrea2 graph")

    node = next((n for n in graph.get("nodes", []) if n.get("id") == MAIN_NODE_ID), None)
    if node is None:
        raise ValueError("Main sampler node 116 was not found")
    if node.get("type") not in {"ClownsharKSampler_Beta", "K2AdvancedSampler"}:
        raise ValueError(f"Unexpected main sampler type: {node.get('type')}")

    old_inputs = {item.get("name"): item for item in node.get("inputs", [])}
    def linked(name: str):
        return old_inputs.get(name, {}).get("link")

    node.update({
        "type": "K2AdvancedSampler",
        "size": [340, 650],
        "inputs": [
            {"localized_name": "model", "name": "model", "shape": 7, "type": "MODEL", "link": linked("model")},
            {"localized_name": "positive", "name": "positive", "shape": 7, "type": "CONDITIONING", "link": linked("positive")},
            {"localized_name": "negative", "name": "negative", "shape": 7, "type": "CONDITIONING", "link": linked("negative")},
            {"localized_name": "latent_image", "name": "latent_image", "shape": 7, "type": "LATENT", "link": linked("latent_image")},
            {"localized_name": "seed", "name": "seed", "type": "INT", "widget": {"name": "seed"}, "link": linked("seed")},
            {"localized_name": "steps", "name": "steps", "type": "INT", "widget": {"name": "steps"}, "link": linked("steps")},
            {"localized_name": "cfg", "name": "cfg", "type": "FLOAT", "widget": {"name": "cfg"}, "link": linked("cfg")},
            {"localized_name": "denoise", "name": "denoise", "type": "FLOAT", "widget": {"name": "denoise"}, "link": linked("denoise")},
            {"localized_name": "preset", "name": "preset", "type": "COMBO", "widget": {"name": "preset"}, "link": None},
            {"localized_name": "schedule_profile", "name": "schedule_profile", "type": "COMBO", "widget": {"name": "schedule_profile"}, "link": None},
            {"localized_name": "correction_strength", "name": "correction_strength", "type": "FLOAT", "widget": {"name": "correction_strength"}, "link": None},
            {"localized_name": "curvature_threshold", "name": "curvature_threshold", "type": "FLOAT", "widget": {"name": "curvature_threshold"}, "link": None},
            {"localized_name": "trust_ratio", "name": "trust_ratio", "type": "FLOAT", "widget": {"name": "trust_ratio"}, "link": None},
            {"localized_name": "local_trust", "name": "local_trust", "type": "FLOAT", "widget": {"name": "local_trust"}, "link": None},
            {"localized_name": "eta", "name": "eta", "type": "FLOAT", "widget": {"name": "eta"}, "link": None},
            {"localized_name": "eta_start", "name": "eta_start", "type": "FLOAT", "widget": {"name": "eta_start"}, "link": None},
            {"localized_name": "eta_end", "name": "eta_end", "type": "FLOAT", "widget": {"name": "eta_end"}, "link": None},
            {"localized_name": "s_noise", "name": "s_noise", "type": "FLOAT", "widget": {"name": "s_noise"}, "link": None},
        ],
        "properties": {
            "Node name for S&R": "K2AdvancedSampler",
            "ue_properties": {"widget_ue_connectable": {}, "input_ue_unconnectable": {}, "version": "7.8"},
        },
        "widgets_values": [0, 8, 1.0, 1.0, "balanced", "native", 0.62, 0.34, 0.34, 0.85, 0.0, 0.25, 0.72, 1.0],
    })

    target_slots = {
        linked("model"): 0,
        linked("positive"): 1,
        linked("negative"): 2,
        linked("latent_image"): 3,
        linked("seed"): 4,
        linked("steps"): 5,
        linked("cfg"): 6,
        linked("denoise"): 7,
    }
    for link in graph.get("links", []):
        if link.get("target_id") == MAIN_NODE_ID and link.get("id") in target_slots:
            link["target_slot"] = target_slots[link["id"]]

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch Full_QualityKrea2.json to use K2 Advanced Sampler")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    args = parser.parse_args()
    output = args.output or args.input.with_name(args.input.stem + "_K2FlowLab.json")

    data = json.loads(args.input.read_text(encoding="utf-8"))
    patched = patch_workflow(data)
    output.write_text(json.dumps(patched, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
