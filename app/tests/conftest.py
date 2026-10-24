"""The D1 dictionary recordings are not part of the public repository; tests that need them are skipped when they are absent."""
import pytest

from fricative.reference import available

NEEDS_D1 = {"test_app.py", "test_ablation.py", "test_audio.py", "test_calibrated.py", "test_classify.py", "test_measure.py",
            "test_phoneme_check.py", "test_plots.py", "test_patterns.py", "test_reference.py", "test_segment.py", "test_segment_alt.py",
            "test_stops.py", "test_validate_calibrated.py", "test_measure_dataset.py"}
collect_ignore = [] if available() else sorted(NEEDS_D1)
