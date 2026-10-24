# Pattern lab (exploration, not part of the app)

Compares one-number CoG with richer spectral patterns for /s ʃ f θ z/ on CMU ARCTIC.
Output: `docs/exploration/spectral-patterns.html`.

Inputs (kept outside the repo, ~27 MB per 300 sentences):
- `x_arctic/tg/<speaker>/arctic_aNNNN.TextGrid` (from `textgrids_8giong.zip`)
- `wav_<speaker>/arctic_aNNNN.wav` (16 kHz, from the Drive folder `cmu_us_<speaker>_arctic/wav`)

Run, with `S` = the folder that holds those inputs. Needs `praat-parselmouth numpy scipy nitime pandas plotly scikit-learn`.

    python fetch_wavs.py ids.tsv "$S/wav_bdl" 300     # ids.tsv = "<name>\t<drive id>" per line
    python extract_tokens.py "$S"                      # writes $S/tokens.pkl (edit SPEAKERS for more voices)
    python analysis.py "$S"                            # cross-speaker accuracy tables
    python make_report.py "$S" docs/exploration/spectral-patterns.html

`analysis.py` evaluates by training on one speaker and testing on another; with more than two
speakers change `cross()` to leave-one-speaker-out. Only two voices (bdl, slt) were used so far.

Variability experiments (spread of each sound, spectral contrast, CoG wobble): `variability.py`, `variability2.py`
(same inputs, `python variability.py "$S"`). `build_reference.py` packs the per-voice statistics the app reads
(`app/assets/reference/arctic_patterns.json`).

Eight-voice work: `loso.py` (leave-one-voice-out), `calibration.py` (matched-rows F2 control, how many calibration tokens are needed),
`train_model.py` (writes `app/assets/model/calibrated_lda.json`, the model behind the Calibrate page).
