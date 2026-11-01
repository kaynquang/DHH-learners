"""Load every model once, before the first recording, so the first child does not wait for it.

The recogniser (wav2vec2, used by the gate, the reconciliation and the GOP score) and the probe on its hidden states are loaded and run
once on a second of noise, which also starts the GPU / the maths libraries. The apps call warm() inside st.cache_resource, so it runs once
per server start and shows a "getting ready" spinner while it does.
"""
from __future__ import annotations

import time

import numpy as np
import parselmouth

from . import calibrated, phoneme_check


def warm() -> dict[str, float]:
    """Seconds each step took ({} entries only for what is available on this machine)."""
    took: dict[str, float] = {}

    def step(name: str, fn) -> None:
        t0 = time.perf_counter()
        fn()
        took[name] = round(time.perf_counter() - t0, 2)

    step("calibrated model", calibrated.load_model)
    step("imports", lambda: [__import__(m, fromlist=["x"]) for m in ("fricative.pipeline", "fricative.gop", "fricative.stops")])
    if phoneme_check.available():
        noise = parselmouth.Sound(np.random.default_rng(0).normal(0, 0.05, 16000), sampling_frequency=16000)
        step("recogniser", lambda: phoneme_check.log_posteriors(noise))
        step("hidden-state probe", lambda: phoneme_check._base(str(phoneme_check.model_dir())))
    return took
