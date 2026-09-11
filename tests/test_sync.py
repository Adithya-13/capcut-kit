from pathlib import Path

import pytest

np = pytest.importorskip("numpy", reason="needs the audio analysis extras")

from capcut_kit.analysis import sync

SR = 16000


def noisy_signal(seconds: float, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    samples = rng.normal(0, 0.05, int(seconds * SR)).astype("float32")
    bursts = rng.uniform(0.2, seconds - 0.3, size=max(3, int(seconds)))
    for start in bursts:
        begin = int(start * SR)
        samples[begin: begin + SR // 10] *= 12.0
    return samples


def test_best_offset_finds_a_known_shift():
    reference = noisy_signal(30.0, seed=1)
    shift_s = 4.0
    excerpt = reference[int(shift_s * SR): int((shift_s + 8.0) * SR)]
    found, confidence = sync.best_offset(reference, excerpt, SR)
    assert abs(found - shift_s) < 0.05
    assert confidence > sync.MIN_CONFIDENCE


def test_unrelated_audio_scores_low_confidence():
    reference = noisy_signal(30.0, seed=1)
    stranger = noisy_signal(8.0, seed=99)
    _, confidence = sync.best_offset(reference, stranger, SR)
    assert confidence < sync.MIN_CONFIDENCE


def test_best_offset_handles_a_needle_longer_than_the_haystack():
    assert sync.best_offset(noisy_signal(2.0), noisy_signal(5.0), SR) == (0.0, 0.0)


def test_best_offset_handles_empty_input():
    assert sync.best_offset(noisy_signal(5.0), np.zeros(0, dtype="float32"), SR) == (0.0, 0.0)


def test_envelope_is_normalised():
    env = sync.envelope(noisy_signal(10.0), SR)
    assert abs(float(env.mean())) < 1e-6
    assert abs(float(env.std()) - 1.0) < 1e-6


def test_refine_skips_clips_too_short_to_match():
    report = sync.refine_one(Path("/tmp/ref.mov"), 0.0, Path("/tmp/clip.mov"),
                             12.0, clip_duration_s=1.0)
    assert not report.accepted
    assert report.offset_s == 12.0
    assert "short" in report.reason


def test_refinement_reports_its_shift():
    report = sync.Refinement(Path("/tmp/a.mov"), 10.0, 10.4, 9.0, True)
    assert abs(report.shift_s - 0.4) < 1e-9
