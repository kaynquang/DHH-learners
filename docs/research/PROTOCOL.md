# SeeSound data collection protocol — DRAFT v0.2 (2026-11-03)

Written by the assistant from the project's state; the points marked **[decide]** are the research team's. Not an ethics document: no approval exists yet.

## 1. Purpose
**Primary question.** How well does the app's three-level verdict (correct / almost / not yet) agree with independent judgements by teachers, for word-initial consonants of the eight lessons (she, see, fee, pea, bee, me, knee, cheat)? **[decide]** if the first aim is rather usability with children.
**Why it matters.** Corpus results (L2-ARCTIC) exist only for an earlier scoring version; the CTC-GOP route and the sustained-hiss route have no independent labels, and nothing has been tested on children or DHH speakers.
**Secondary.** (a) How often the app cannot score (quality gate, no speech, unsure). (b) Agreement between teachers (a ceiling for any tool). (c) How verdicts differ by word and by participant group.
**Not claimed.** Learning effect, usability, or that stars/unlock order mean mastery.

## 2. Participants **[decide all]**
Deliberately small: a **pilot**, not a powered study. Suggested: 2-3 adults first (to test the procedure), then about 5-10 learners, DHH learners only with approval and consent **[decide]**. With so few recordings the results are descriptive (counts, agreement with its interval); no claim of accuracy for a population is made. Each participant gives 16 recordings (8 words x 2), about 4 minutes; two teachers rate them (about 15 minutes each per participant, can be split over days).
Participants are known by a **code** (S01...), never by name. No camera is used in the collection mode.

## 3. Procedure (what the teacher does)
1. Quiet room, microphone about 10-15 cm from the mouth, same device for the whole session. Note device and room in the session sheet.
2. Open https://collect.seesound.org/?page=collect (the hosted learner app; sign in with your e-mail). Enter the participant code and your initials; tick that consent was given and, if given, that the audio may be kept.
3. The app shows the eight words one at a time, each twice (16 takes), in a fixed order. The participant presses the blue microphone button and says the word. **No verdict is shown.** A take that is too quiet, too loud, or too noisy is refused and repeated (these are logged).
4. At the end: download the participant's zip, or later all data from the Dev app, page "Rate".
5. At least two teachers rate each recording on the Dev app page "Rate": audio only, the target word shown, the app's verdict hidden, order randomised per rater; they choose correct / almost / not yet and may tick "not sure".

## 4. What is stored (all on the local computer)
`logs/collect/<code>/session.json` (consent confirmer's initials, audio consent, app commit), `takes.jsonl` (word, take, quality numbers, the app's verdict and measures), `audio/*.wav` only if audio consent was given, and `logs/collect/labels.jsonl` (ratings). Nothing is sent anywhere. A participant's data can be deleted from the "Rate" page.

## 5. Analysis (fixed before looking at data)
- Per route (word route: she/see/fee; GOP: pea/bee/me/knee/cheat) and per word: confusion matrix app x rater, exact agreement, Cohen's kappa and linear-weighted kappa; the app's "not scored" takes reported as a separate count, never dropped from the denominator.
- Rater-rater agreement computed the same way; the app is compared with each rater and, where raters agree, with their consensus **[decide: consensus rule]**.
- With a pilot this small, a route can only be called *worth studying further* (not *validated*) if its weighted kappa with the raters approaches the rater-rater value **[decide: threshold]** and its false-"not yet" rate on correct takes is low.
- Quality-gate refusals and unscored takes are reported by word and by group.

## 6. Ethics and data **[decide, required before children]**
Approval number and body; information sheet and consent/assent forms (adult, parent/guardian, child assent); who stores the data, for how long, who may listen; anonymisation (codes only, audio of children is personal data); right to withdraw and delete. This draft stores audio only after an explicit consent tick and never stores names.

## 7. Limits to state in any report
Thresholds in the app were set on one adult; the recogniser was trained mostly on hearing speakers; the lesson order and star rules are not part of this collection; rating is by listening and is subjective; a few raters.

## 8. Recommended decisions (the assistant's recommendations, to be confirmed or changed by the research team)
| Point | Recommendation |
|---|---|
| First aim | Agreement between the app's verdict and teachers' ratings |
| Participants | Pilot: 2-3 adults to test the procedure, then 5-8 hearing EFL learners |
| DHH participants | Later stage, only with approval and consent |
| Raters | Two teachers (one may be a foreign-language teacher) |
| Consensus rule | Compare the app only with recordings on which both raters agree; recordings with rater disagreement are counted and reported separately, not dropped |
| "Worth studying further" | Weighted kappa between the app and the raters of at least about 0.6 and not far below the value between the two raters (0.6 is a conventional "substantial" level; the team may choose another) |
| Audio | Kept only with the separate consent tick; deleted after 1 year (the 1-year period is a suggestion) |
| Who may listen | The two raters and the research team; audio is not sent by e-mail or chat |
| Ethics | Ask the department/school (HUFLIT and NFU) whether this small pilot needs formal approval before recording learners; adults on the team can pilot the procedure first |

## 9. When to record again, and who sees what (added 2026-11-03)
- **Record again only for a technical reason**: too quiet, too loud, too much noise (the app refuses these by itself), or a disturbance (cough, noise, wrong word said), for which the teacher presses "Undo the last recording". A take is **never** repeated because the pronunciation seemed poor: that would keep only the good takes and bias the agreement. The app shows no verdict to the participant or the teacher during recording.
- Refused recordings are counted with their reason (no audio kept); after three refusals in a row the teacher may skip the word, and the skip is reported.
- **Teachers/raters** only rate, blind to the app. **The person who keeps the data (Kiet)** sees the app's verdicts, the agreement with each rater, and the list of takes where they disagree (Dev app, "Rate" > "Agreement"), and exports the CSV for analysis. Raters see the comparison only after all ratings are in, if the team decides to discuss the disagreements.

## 10. Where the data go (added 2026-11-03)
The app is hosted at collect.seesound.org / admin.seesound.org behind Cloudflare Access (invited e-mails only; see docs/deploy/DEPLOY.md); recordings and logs are on the server managed by Kiet. After a session the teacher downloads the participant's zip and uploads it to the team's Google Drive folder (restricted access). The consent form v0.6 says this; the department/ethics decision should confirm it, and the Drive folder must not be open to "anyone with the link".
