# RAG Red-Team Arena

## Milestone 1: Recorded case explorer

Implement the supervisor's M1 app shell, JSON challenge loader and passage
display, using Streamlit and the existing research package. Enrich this first
screen with already available recorded answers and rule traces so it can show
the measured contribution and known failure without new inference. This is
an engineering deliverable, not another efficacy experiment.

The initial collection is all 24 authored fictional EXP-044 challenges, with
their original one or two passages. Preserve exact source order and text.
The three recorded arms are S1, Original NS and Candidate NS. Original NS must
never be relabeled S2: the EXP-044 experiment did not run self-verification.

The app is explicitly a recorded replay. Loading it never imports MLX, downloads
a model, generates an answer or writes to historical experiment files. Serving
is local to 127.0.0.1. A separate pinned UI environment leaves the research
inference environment unchanged.

## Screen and interactions

- Select any of the 24 challenges; filter by six source-mechanism families.
- Shortcuts show a recovered correct answer, conflicting sources and a false
  source that the verifier accepted.
- Display the question, complete ordered sources and three verbatim answers.
- Distinguish release/withhold decisions from correctness under the authored
  fictional reference. A reveal toggle controls reference and exact-score
  display. VERIFIED means source consistency, not independent factual truth.
- Display the actually fired candidate rule, matching source quotations,
  independently parsed answer and unchanged neural facts. Do not fabricate
  pass/fail statuses for rules that were not executed.
- UNKNOWN visibly remains unresolved. Out-of-format drafts retain their
  EXP-044 UNSCORABLE label; the later AI semantic labels do not replace it.
- Display recorded stage time/token counts as historical measurements, not
  current UI latency. Export a full case JSON with raw model strings, prompts,
  provenance and the original exact score.
- Keep the false-source failure visible and understandable in the presentation.

## Data contract

`load_challenges(root) -> list[dict]` validates pinned EXP-044 raw, fixture,
manifest and summary hashes; returns 24 ordered challenge records. Candidate
decisions are replayed through the shared verification module and must match
the saved trace before any challenge is displayed. An integrity failure blocks
the UI rather than silently serving mismatched evidence.

Each record exposes `case_id`, `question`, ordered `documents`, `family`,
`authored_reference`, `systems` and `raw_record`. Each system exposes its real
`system_id`, display `name`, verbatim `answer`, optional source `verdict`,
`action`, exact `score`, `trace`, recorded `latency_seconds`, input/output token
counts and `recorded=true`. The full raw record is retained for download.
Reference truth is display metadata and never an input to verifier replay.

## M1 acceptance checks

1. Loader exposes all 24 unique questions and all three correctly named arms;
   original source order, answer text and exact scores are preserved.
2. A corrupted source or altered saved candidate trace is rejected.
3. The false-source example is simultaneously source-VERIFIED and exact-score
   WRONG; the UI explains this distinction. A conflict shows its actual rule
   and both source quotations; an unresolved answer stays UNKNOWN.
4. App starts locally; browser navigation, filtering, shortcuts, reference
   reveal and JSON export work. Desktop and mobile layouts remain readable.
5. Loader and UI tests do not load a model or modify historical results.

## Later milestones from the supervisor plan

| Milestone | Remaining scope after M1 |
|---|---|
| M2 Three systems | Live shared interface for standard RAG, S2 self-review and neuro-symbolic verification; all challenges render actual three-arm outputs. Recorded Original NS is not this requirement. |
| M3 Attack editor | Free-text inserted passages, six attack templates, insertion position and optional local AI attacker. New inputs require actual new runs, not reuse of cached answers. |
| M4 Proof panel | Complete fact graph, executed-rule display, offending-passage highlighting, and a demonstrated REFUTED case. M1 contains only the available recorded trace preview. |
| M5 Rounds and scores | SQLite persistence, per-system/attack scoring, JSONL exports, rate limits, participant entry and the supervisor's concurrency/counting checks. |

Live attack success rates, costs per 1,000 queries, collected human attacks,
video and user study remain unmeasured. M1 screenshots are UI artifacts, not
proof of general hallucination reduction or completion of the full Arena.
