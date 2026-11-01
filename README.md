# DHH-learners

Visual pronunciation feedback for deaf and hard-of-hearing (DHH) learners of English consonants. A learner records one word; the app locates the consonant, measures it, and returns a three-level judgement (◯ correct, △ almost, ✕ not yet) together with a spectrogram, numerical measures and a written tip.

Prototype for the FTIP project at National Formosa University (supervisor: Prof. Hui-Kai Su).

## What it does

Eight target sounds, each with its own words and scoring method:

| Sound | Words | How it is scored | Module |
|---|---|---|---|
| /s/ /ʃ/ /f/ | see, sip, sun · she, ship, shoe · fee, fan, food | Praat-style CoG and relative amplitude with thresholds; with the optional recogniser, the recogniser decides *which* sound was produced and the measures decide the *degree* | `fricative/classify.py`, `fricative/phoneme_check.py` |
| (same) | | Optional learner calibration (six recordings of see/she/fee) and a trained LDA | `fricative/calibrated.py` |
| /p/ /b/ | pea, bee | Voice onset time (VOT) rule; with the recogniser, a linear probe on wav2vec2 features | `fricative/stops.py` |
| /m/ /n/ | me, knee | Phone recogniser at the nasal | `fricative/nasals.py` |
| /tʃ/ | cheat | Probe on the hiss (hand-crafted rise-time LDA as fallback) | `fricative/affricate.py` |

A "kind-of-sound" gate (`phoneme_check.first_consonant`) withholds scoring when the recording starts with a different kind of sound than the target (for example a fricative for a stop word).

Pages: **Practice** (record or upload, verdict, then switchable views: Compare, Patterns, Detectors, Phoneme check), **Calibrate**, **How it works**.

## Evidence and limits

Everything is experimental. Numbers come from running speech cut into pseudo-words (CMU ARCTIC, L2-ARCTIC), not from isolated words and not from DHH speakers. On annotated learner errors, fixed thresholds validated on native voices rejected 45% of correctly produced /s/ and /ʃ/; the recogniser-assisted design reduced this to 8% and 3% while keeping 100% and 88% of the annotated confusions. /f/–/θ/ cannot be told apart from the hiss alone, and several sounds have too few annotated learner errors to evaluate. See `explore/pattern_lab/README.md` for the experiments.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r app/requirements.txt
.venv/bin/streamlit run app/streamlit_app.py
```

Open http://localhost:8501. Browsers only allow the microphone on HTTPS or `localhost`.

### Optional: the phone recogniser

```bash
.venv/bin/pip install -r app/requirements-recogniser.txt
# download facebook/wav2vec2-xlsr-53-espeak-cv-ft (Apache-2.0) into app/assets/model/w2v_phone
# (needs pytorch_model.bin and vocab.json), or point W2V_DIR at the folder
export W2V_DIR=/path/to/xlsr53espeak
.venv/bin/streamlit run app/streamlit_app.py
```

The Phoneme check view, the identity decision for fricatives, the stop and affricate probes, the nasal scorer and the kind-of-sound gate appear only when the checkpoint is found. Without it, /m/ and /n/ cannot be scored, and the other sounds use the threshold and VOT rules.

### D1 samples

The D1 dictionary recordings (`SOUNDS/`) and their manual boundaries (`boundaries.csv`) are not part of this repository. Without them the Sample input, the Compare view and the How it works illustration are hidden, and the tests that need them are skipped. To use them, place them at the repository root with columns `file,phone,accent,start_s,end_s,manual_cog_hz`.

## Test

```bash
cd app && ../.venv/bin/python -m pytest -q
```

## Layout

| Path | What it is |
|---|---|
| `app/streamlit_app.py` | Entry point and navigation |
| `app/app_pages/` | Practice, Calibrate, How it works |
| `app/views/` | The switchable Practice views |
| `app/fricative/` | Core logic without Streamlit: audio, segmentation (`segment.py`, `segment_alt.py`), measures, scorers, recogniser wrapper, plots |
| `app/assets/` | Trained model weights (small JSON), articulation images, reference statistics |
| `app/validate_calibrated.py` | Score a folder of isolated-word recordings (`<speaker>_<word>_<n>.wav`) with the calibrated model |
| `explore/pattern_lab/` | Research scripts that produced the numbers and the model files (need ARCTIC and L2-ARCTIC; not included) |

## How it is implemented

1. **Audio.** Parselmouth (Praat in Python) decodes wav or mp3, mixes to mono and keeps the first five seconds.
2. **Locating the consonant.** For fricatives the onset is the start of the run of 2.5–12 kHz energy at least 15 dB above the recording's own noise floor, and the offset is the first voiced frame (`segment.py`). For stops the burst is found in the 1.5–7.5 kHz band and VOT is the time to the first voiced frame (`stops.py`).
3. **Measuring.** CoG on the middle 50% with a rectangular window and power 2 (matches manual Praat measurements), relative amplitude against the following vowel, spectral shape features (`measure.py`, `patterns.py`).
4. **Recogniser.** Posteriors of the phone recogniser are pooled per sound class over the consonant (`phoneme_check.py`); linear probes on layer-8 hidden states are stored as JSON in `app/assets/model/`.
5. **Fusion.** `phoneme_check.reconcile` combines the measured verdict with the recogniser: a different sound heard gives ✕, the intended sound heard with disagreeing thresholds gives △.
6. **Views.** Each view is a module in `app/views/` with `render(ctx)`; `practice.py` builds a `Ctx` and lets the learner switch between them.

### Adding a sound or a word

- *A word for an existing sound:* add it to `TARGETS` (or the matching dictionary) in `app/fricative/config.py`.
- *A new sound:* write a scorer module that returns a `Verdict` (see `classify.py`), register its words in `config.py`, and add a branch for it in `app/app_pages/practice.py` (see the stop, nasal and affricate branches). Put the evaluation script in `explore/pattern_lab/` and test the scorer in `app/tests/`.
- *Retraining a model:* run the matching script in `explore/pattern_lab/` (for example `train_model.py`, `train_other.py`, `train_ch_probe.py`); each writes its JSON into `app/assets/model/`.

## Data and licences

CMU ARCTIC and L2-ARCTIC are third-party corpora with their own licences and are not redistributed. The recogniser checkpoint is facebook/wav2vec2-xlsr-53-espeak-cv-ft (Apache-2.0).
