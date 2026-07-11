from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("patch_workflow", ROOT / "tools" / "patch_workflow.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture():
    inputs = [
        {"name": "model", "link": 159},
        {"name": "positive", "link": 157},
        {"name": "negative", "link": 158},
        {"name": "latent_image", "link": 160},
        {"name": "sigmas", "link": None},
        {"name": "guides", "link": None},
        {"name": "options", "link": None},
        {"name": "steps", "link": 167},
        {"name": "denoise", "link": 176},
        {"name": "cfg", "link": 175},
        {"name": "seed", "link": 161},
    ]
    links = [
        {"id": 159, "target_id": 116, "target_slot": 0},
        {"id": 157, "target_id": 116, "target_slot": 1},
        {"id": 158, "target_id": 116, "target_slot": 2},
        {"id": 160, "target_id": 116, "target_slot": 3},
        {"id": 167, "target_id": 116, "target_slot": 7},
        {"id": 176, "target_id": 116, "target_slot": 8},
        {"id": 175, "target_id": 116, "target_slot": 9},
        {"id": 161, "target_id": 116, "target_slot": 10},
    ]
    return {
        "nodes": [{"id": 188, "type": "PiDUpscale", "widgets_values": ["2kto4k", "flux2", True, "bf16", "4x", 0.2]}],
        "definitions": {
            "subgraphs": [{
                "id": MODULE.MAIN_SUBGRAPH_ID,
                "nodes": [{
                    "id": 116,
                    "type": "ClownsharKSampler_Beta",
                    "inputs": inputs,
                    "outputs": [],
                    "properties": {},
                    "widgets_values": [],
                }],
                "links": links,
            }]
        },
    }


def test_patcher_rewires_sampler_and_preserves_pid():
    source = fixture()
    result = MODULE.patch_workflow(source)
    graph = result["definitions"]["subgraphs"][0]
    node = graph["nodes"][0]
    assert node["type"] == "K2AdvancedSampler"
    assert [item["name"] for item in node["inputs"][:8]] == [
        "model", "positive", "negative", "latent_image", "seed", "steps", "cfg", "denoise"
    ]
    slots = {link["id"]: link["target_slot"] for link in graph["links"]}
    assert slots == {159: 0, 157: 1, 158: 2, 160: 3, 161: 4, 167: 5, 175: 6, 176: 7}
    assert result["nodes"][0]["widgets_values"] == ["2kto4k", "flux2", True, "bf16", "4x", 0.2]
    assert source["definitions"]["subgraphs"][0]["nodes"][0]["type"] == "ClownsharKSampler_Beta"


def test_patcher_rejects_unexpected_workflow():
    broken = fixture()
    broken["definitions"]["subgraphs"][0]["nodes"][0]["type"] = "UnknownSampler"
    try:
        MODULE.patch_workflow(broken)
    except ValueError as exc:
        assert "Unexpected" in str(exc)
    else:
        raise AssertionError("patcher accepted an unsupported workflow")
