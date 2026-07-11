# Verification

This repository is continuously checked in two ways:

1. Unit and sampler-contract tests validate scheduler monotonicity, one model call per step, constant-flow integration, preset behavior, trust-region safety, and guarded workflow rewiring.
2. A second CI job clones the current official ComfyUI, installs this repository exactly under `custom_nodes/ComfyUI-Krea2-FlowLab`, and runs `verify_install.py`.

This file was added through the CI-verification pull request so the initial public release is validated by a pull-request workflow whose jobs and logs can be inspected before merge.
