import numpy as np
import parselmouth

from fricative.noise import check, noise_floor_db, speech_level_db


def _sound(amplitude: float, seconds: float = 1.0, fs: int = 16000):
    rng = np.random.default_rng(0)
    return parselmouth.Sound(rng.normal(0, amplitude, int(seconds * fs)), sampling_frequency=fs)


def test_louder_noise_has_higher_floor():
    assert noise_floor_db(_sound(0.01)) > noise_floor_db(_sound(0.001)) + 15


def test_floor_ignores_a_short_click():
    quiet = _sound(0.001)
    x = np.asarray(quiet.values).reshape(-1).copy()
    x[8000:8200] = 0.5
    clicked = parselmouth.Sound(x, sampling_frequency=16000)
    assert abs(noise_floor_db(clicked) - noise_floor_db(quiet)) < 1.0


def _word_in_room(room_amp: float, word_amp: float):
    """1.5 s of room noise with a burst of 'voice' (noise as well) in the middle."""
    rng = np.random.default_rng(1)
    x = rng.normal(0, room_amp, 24000)
    x[8000:14000] += rng.normal(0, word_amp, 6000)
    return parselmouth.Sound(x, sampling_frequency=16000)


def test_recording_quality_cases():
    from fricative.noise import recording_quality
    assert recording_quality(_word_in_room(0.001, 0.1)).problem is None
    assert recording_quality(_word_in_room(0.02, 0.05)).problem == "noisy"
    assert recording_quality(_word_in_room(0.00005, 0.0005)).problem == "quiet"
    loud = np.asarray(_word_in_room(0.001, 0.1).values).reshape(-1).copy()
    loud[9000] = 1.0
    assert recording_quality(parselmouth.Sound(loud, sampling_frequency=16000)).problem == "loud"


def test_verdicts():
    noise = noise_floor_db(_sound(0.001))
    assert check(noise, _sound(0.002)).verdict == "noisy"
    assert check(noise, _sound(0.2)).verdict == "good"
    assert speech_level_db(_sound(0.2)) > noise


def test_a_clip_that_is_all_voice_uses_the_room_the_recorder_measured():
    """A guided recording can be voice from the first 0.2 s to the last: its own 10th percentile is then the voice, not the room (log of 18:48: 8 dB for a voice 15 dB over the room)."""
    from fricative.noise import recording_quality
    rng = np.random.default_rng(2)
    voice = parselmouth.Sound(rng.normal(0, 0.05, 48000) * (1 + 0.15 * np.sin(np.arange(48000) / 300.0)), sampling_frequency=16000)   # 3 s, level swings a little
    assert recording_quality(voice).problem == "noisy"                       # alone, the clip looks like 'voice over voice'
    assert recording_quality(voice, room_db=-50.0).problem is None           # the recorder heard the room at -50 dBFS
