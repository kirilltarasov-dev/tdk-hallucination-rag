# Arena milestone M1 completed

Completed 2026-11-18 as an engineering milestone, not an efficacy experiment.
The app starts locally, loads all 24 EXP-044 challenges, displays their original
ordered sources, and provides a working recorded-results explorer. This meets
M1's app-shell/challenge-loader/passage-display acceptance scope. The complete
live Arena described by the supervisor remains unfinished.

## What is available

- Streamlit 1.67.0 frontend in `demo/app.py`, with a separate pinned UI environment.
- Integrity-checked challenge loader in `src/arena/replay.py` and actual replay
  through the shared independent-answer verifier.
- All 24 questions and six source families; three faithfully named recorded
  arms: S1, Original NS and Candidate NS. The latter two share the same draft.
- Source text, fictional reference reveal, verbatim answers, unchanged exact
  scores, fired rule, matching quotations and retained neural facts.
- Visible VERIFIED-but-WRONG false-source example, source conflict and UNKNOWN.
- Full case JSON download including original prompts, outputs and source hashes.
- Desktop and mobile screenshots under `results/figures/arena_m1_*.png`.

The UI does not relabel Original NS as S2, manufacture live results, treat
unexecuted rules as passed, or replace UNSCORABLE with AI semantic labels.
New model calls, generated experimental outputs and measured attack rates: zero.

## Checks actually completed

All 121 standard-library Python tests passed, including six new loader/export
checks. These verify complete case coverage, original answer and source-order
preservation, corruption rejection, changed-trace rejection, the false-source
boundary, conflict evidence and UNKNOWN/UNSCORABLE preservation.

The running app returned a healthy response on `127.0.0.1:8501`. The Playwright
browser check passed: three arm names, all six filters, Previous/Next, all three
showcase shortcuts, conflict rule, reference toggle, full JSON download, mobile
width and zero browser exceptions. The reference toggle was exercised through
keyboard interaction with its accessible switch. Desktop (1440 × 1180) and
mobile (390 × 844) screenshots were visually inspected; no clipping or
horizontal page overflow remained. A first screenshot revealed a clipped top
caption; layout padding was corrected before the saved acceptance screenshots.

`pip check` passed in `.venv-arena`. The research inference environment was not
modified. The loader verifies the original EXP-044 raw/manifest/summary hashes
and its fixture hash, then compares the current candidate replay with the
complete saved trace. Historical experimental outputs remain unchanged.

## Supervisor checklist implications

| Original requirement | Current status | Reason |
|---|---|---|
| P1-35 Replace the literature assistant with the Arena | Partial | Arena M1 now exists; the live game is incomplete. |
| P1-36 Build M1–M5 with acceptance tests | Partial | M1 passes its checks; M2–M5 remain open. |
| P1-38 Full per-question audit trace | Partial | Recorded traces can be inspected/exported; live round logging is not built. |
| P1-39 Demo video and manuscript screenshot | Partial | Verified screenshots exist; video and insertion into the manuscript remain open. |

No entire multi-milestone checklist item is marked Done merely because the
initial explorer is usable. P0 completion counts are unchanged. The old
2026-11-17 percentage audit remains a dated snapshot and should not be presented
as a fresh full-plan recount.

## Remaining boundary

M2 needs actual Standard RAG/S2/NS execution through one app interface. The
current challenge collection has one or two supplied passages, not the final
five-passage round design. M3 adds attack construction and live evaluation.
M4 still needs a fact graph, full executed-rule presentation and a demonstrated
REFUTED example. M5 needs round persistence, audience participation, scoring
and concurrency checks. Public serving, a recorded video, human attacks and
a user study have not been performed.
