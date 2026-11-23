# ECEI 2027 paper: changelog

## v0.1 (2026-11-03)
- New short version (8 pages incl. references) from the long IEEE version `../ieee_long/v1`, in the MDPI template (class option `engproc`).
- Kept: abstract, introduction, related work (shortened), system design, three assessment routes, L2-ARCTIC fricative results, CoG AUC table, limitations, planned user evaluation.
- Cut or condensed (still in `ieee_long/v1`): stop/context-leakage sections and figures, Table of 8 sounds, researcher-app figure, GOP verdict table (now one sentence), full per-sound tables, extra related work.
- Open items: department, corresponding e-mail, funding, ethics, author contributions (all red `\tbd{}`); CAPT/GOP/UDL references; check page limit and template rules with the organisers; stand-in blank logos replace the MDPI EPS logos (no Ghostscript here).

## v0.2 (2026-11-03), reader-oriented pass, 8 pages
- Read the PDF page by page as a reader. Added what a reader needs: a short note on how to read Fig. 1, a sentence before Table 1 saying what it shows, a plain "A good route has a low FR and a high Det." line, and a lead sentence for each Discussion paragraph (Main finding / Design questions / Limitations).
- Section 5 restructured as question, evidence, so-what: 5.1 fricatives (Table 2), 5.2 other sounds and the replaced probes (numbers moved from a dense list into prose, with the GOP counts and the clear statement that they are not accuracy), 5.3 live cues (Table 3, with "AUC 0.5 is chance" in the caption).
- Fig. 1 redrawn larger and extended into the margin; Fig. 2 reduced to two readable panels (home, lesson result); Fig. 3 smaller; figures now float instead of leaving gaps.
- Cut to stay at 8 pages: GOP count table, "other contrasts" table, Functional-checks subsection (one sentence kept in Discussion), shortened related work, references abbreviated.
- Note: `v0.1` was edited after it was created (it is the first version of this session's work, not a frozen copy); treat `v0.2` as the reference. Open items unchanged (all red TBD, CAPT/GOP/UDL references, page limit and template to confirm with the organisers).

## v0.3 (2026-11-03), IMRAD structure (MDPI order)
- 1 Introduction (1.1 Background, 1.2 Related Work, 1.3 The Present Study); 2 Materials and Methods (system and learner workflow, recording and live guidance, lip cues/Sound Check/data handling, the three assessment routes, evaluation design); 3 Results (fricatives, other sounds, live cues); 4 Discussion (main finding, design questions, limitations, planned user evaluation); 5 Conclusions.
- Moved the evaluation protocol (evidence types, metrics) out of the old "Technical Evaluation and Results" into Methods; "Planned User Evaluation" is now a paragraph of the Discussion. Roadmap sentence uses labels, not fixed numbers. Still 8 pages.
- v0.2 left as it was (previous structure).
- Author info: Hui-Kai Su, Department of Electrical Engineering, NFU, hksu@nfu.edu.tw (given by the user 2026-11-03); departments of the other two authors still to confirm.
- Affiliations: K.P. and Q.N. at HUFLIT (Vietnam), H.-K.S. at NFU Electrical Engineering (given by the user). The earlier acknowledgement/funding line (FTIP, NFU) still to be reviewed.
- Departments: K.P. Foreign Languages, Q.N. Information Technology (HUFLIT); wording of department names is the assistant's, to confirm.
## v0.4 (2026-11-03): Table 1 reformatted (left-aligned, row rules, narrower columns); copied from v0.3.
- v0.4: removed the running header (Version ... submitted to) and DOI footer (AtBeginDocument override in main.tex); back to 8 pages.

## v0.5 (2026-11-03): line numbers removed (
olinenumbers after egin{document}; MDPI 'submit' adds them by default). Put them back if the organisers ask for a review copy with line numbers. Copied from v0.4.
