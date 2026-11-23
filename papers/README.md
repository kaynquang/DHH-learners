# Papers: versions

Each venue has its own folder, each draft its own `vX.Y` subfolder (frozen once sent or reviewed; edit a copy as the next version). Build with `latexmk -pdf main.tex` inside the version folder (MDPI: no shell-escape needed because the EPS logos have stand-in PDFs in `Definitions/`).

| Folder | Venue / template | Pages | Status |
|---|---|---|---|
| `ieee_long/v1` | IEEEtran, long technical version (12 pp.); source of truth for details, tables and figures cut from the short versions; also in `../overleaf_paper` (working copy) | 12 | kept for the future |
| `ecei2027/v0.1` | same, first draft (superseded) | 8 | superseded by v0.2 |
| `ecei2027/v0.5` | 10th Eurasian Conference on Educational Innovation (ECEI 2027), Engineering Proceedings, MDPI template (`engproc`) | 8 | current, 2026-11-03 |

ECEI facts from the conference page (2026-11-03): 29-31 Jan 2027, Malaysia, hybrid; abstract due 15 Nov 2026, full paper from 30 Nov 2026, early registration and full paper 31 Dec 2026. Page limit and template are NOT stated on the page: check the submission system (ocs.ecei.asia) and the organisers before submitting.
