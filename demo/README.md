# RAG Red-Team Arena

The Arena offers a recorded explorer (M1), explicit local generation (M2),
a source attack editor (M3), an auditable proof view (M4), and a persisted round
ledger with local audience controls (M5).
Recorded mode compares the saved EXP-044 Standard RAG draft, Original NS and
Candidate NS. Live mode generates Standard RAG, S2-style same-model review and
neuro-symbolic answers from one shared draft. Original NS in recorded mode is
not S2 self-verification.

## Start locally

From the repository root, create a separate Python 3.12 environment once:

```bash
python3.12 -m venv .venv-arena
.venv-arena/bin/python -m pip install -r requirements-arena.txt
```

Start the app:

```bash
.venv-arena/bin/python -m streamlit run demo/app.py --server.address 127.0.0.1 --server.port 8501
```

Open <http://127.0.0.1:8501>. Stop the server with Ctrl+C in its terminal.
After updating Python modules, restart the server so imported functions do not
remain cached from an older build.
The version lock is `requirements-arena.lock`; it is a Python 3.12/macOS arm64
package snapshot without wheel hashes, not a tested Linux release. It does not
alter the existing `.venv` inference environment. Model weights and MLX are
not required for recorded mode. Live mode uses the existing research `.venv`
and cached pinned Mistral model. It never downloads weights automatically;
a missing inference environment/cache produces an error.

## Run a live round

Select **Live local run**, choose a challenge, then press **Run three systems
locally**. This performs exactly three bounded local calls: S1 draft (128 output
tokens maximum), S2 review (128), and V3 extraction for NS (1,024). S2 and NS
receive the same draft. The fictional reference is used only after generation
for the displayed exact score.

Results appear with actual stage measurements and can be downloaded. Switching
questions, modes or reference visibility makes no new calls. Returning to an
already run input in the same session shows that round; pressing Run again
creates a new uniquely identified round. A result is never shown for different
ordered inputs. Overlapping model runs are rejected by a local lock.

Raw calls, manifest, result and completion hashes are saved under
`results/arena_runs/<run_id>/`. Failed/partial runs remain there too. This folder
is ignored by Git; retain/export any rounds needed for future research. These
are demo records, not additions to the frozen EXP-044 evaluation. The measured
one-round integration sample is archived under `results/demo/arena_m2_smoke/`.

## Edit the sources

In live mode expand **Attack editor**, enable **Insert an attack passage**, and
enter free text or load one of the six templates. Choose its insertion position.
Commit a text edit by leaving the field or pressing Ctrl+Enter / Cmd+Enter.
The sources below display the exact input. Blank or oversized enabled passages
block evaluation. Disable insertion to restore the original context.

**Ask local AI for an attack** makes one separate call (up to 256 output tokens)
and fills the editor. It receives only the question and original sources. Review
or edit the suggestion, then press **Run three systems locally** to evaluate it.
Neither editing nor selecting a template invokes a model. Changing the text or
position hides results for other inputs; returning to an identical ordered input
may show its existing session result.

Templates are editable proposals, not established successful attacks. Their
origin label describes how editing started, not a verified classification of
user modifications. Ordinal, numeric and correction claims can exceed the
current verifier grammar. UNKNOWN does not establish attack resistance.

Edited rounds save `attack.json` and `attack_integrity.json` alongside their raw
calls. These record base context, exact inserted text, position, source ID and
optional AI proposal run ID, with hashes binding provenance to the result.
The case download includes the same attack metadata. Each AI proposal has its
own separate run directory. Replay either kind without inference:

```bash
python3 -B -m src.arena.worker --replay results/arena_runs/RUN_ID
```

## Inspect the proof

Recorded and completed live rounds include **Proof graph and executed checks**.
The graph links supplied sources, validated neural facts, the question frame,
the independently parsed draft and the final decision. Deterministically audited
negations have separate nodes. All retained facts remain visible, including
facts outside the target event/year; invalid extraction produces no fact nodes.

The stage checklist distinguishes PASSED, BLOCKED, NOT REACHED and other actual
trace statuses. It reports emitted rule IDs, not an instrumented log of every
branch condition. Source selection links the graph to full passages; highlighted
quotations are rule witnesses. Whole-source diagnostic highlights indicate an
extraction/audit problem, not that the source is factually false. The graph and
checks can be downloaded with their underlying trace and raw extraction.

Select **Proof examples** for two pinned walkthroughs requiring no inference:

- **Answer mismatch** replays the actual EXP-040 E040-018 draft and its historical
  V2 extraction through the current candidate. “Velvet Otters won.” disagrees
  with the source's “Velvet Otters 19”, so R6_ANSWER_MISMATCH yields REFUTED.
  This is retrospective replay, not a fresh V3 run or an EXP-044 observation.
- **Extraction failure** replays the actual M3 attack round. Null fact fields
  fail extraction validation, so source auditing is not reached. UNKNOWN is
  not a symbolic refutation or measured attack resistance.

Both examples have full provenance downloads. The examples are diagnostic
illustrations, not a representative evaluation sample. REFUTED means mismatch
with supplied evidence under the declared rules, not external factual falsity.

## Round ledger and entry

Select **Round ledger** to inspect exact outcome counts by system and attack
origin. Live, archived demo and software-simulation populations remain separate.
CORRECT, WRONG, ABSTAIN and UNSCORABLE are separate counts. A proposal is not an
evaluation round; admission rejections and infrastructure failures are not wrong
answers. Reopening a completed run does not add another round. These are
self-selected demonstration counts, not an attack success or efficacy estimate.

The view and its JSONL export use one SQLite snapshot. The attack-origin filter
changes the table only; export includes every attempt in the selected population,
full completed payloads, scores and provenance. Downloads do not rerun the app.
**Refresh ledger** explicitly refreshes the snapshot.

Both inference buttons register an attempt before calling the worker. Limits are
six accepted requests per anonymous session per ten minutes, thirty globally per
hour, and one active request at a time. A 240-second admission lease expires on a
later admission attempt after a crash; worker timeout is 180 seconds. The worker's
file lock still prevents overlapping model execution. A missing/failed ledger
blocks new UI inference. These anonymous session IDs are not authenticated users;
resetting a session does not bypass the global quota.

SQLite defaults to `results/arena_state/arena.sqlite3`, ignored by Git. Set
`TDK_ARENA_DB` before server startup to use a separate file. Preserve raw run
folders as well as the ledger. If persistence fails after generation, raw logs
remain available, the UI reports failure, and no automatic retry occurs.
Previously completed M2/M3 engineering examples can be explicitly imported once:

```bash
python3 -B -m src.arena.service --import-archives
```

This verifies existing raw artifacts, adds two evaluations and one AI proposal
to **Archived demo examples**, and makes no model calls. Repeating the command
is idempotent. It never adds historical examples to the live population.

The entry section provides a link and QR. The default `http://127.0.0.1:8501`
works only on this computer. To prepare a venue link, an organizer can set
`TDK_ARENA_PUBLIC_URL` to a reachable HTTP(S) URL before startup. This setting
only changes the link/QR: it does not publish the app or change its localhost
binding. Phone access, actual venue networking and a supervised audience run
still require separate checks.

## A two-minute recorded walkthrough

1. Select **Recovered answer**. The source says “took first place.” Candidate
   NS releases the correct saved draft while Original NS abstains. Expand the
   trace to see the source quotation and fired rule.
2. Select **Source conflict**. Both passages name a different winner. The
   candidate abstains and shows `R5_CONFLICT` with both matching facts.
3. Select **False source**. Both NS variants say VERIFIED, but the saved answer
   is WRONG against the authored fictional reference. Point out the explicit
   source-consistency limitation.
4. Use **Wrong-year evidence** in the sidebar to inspect an UNKNOWN result.
   The original S1 score remains UNSCORABLE where its text violates the frozen
   output contract. Toggle the fictional reference to show or hide exact scores.
5. Download a case to inspect all original prompts, raw model strings, timings,
   source hashes and decisions. The export contains the reference answer too.

The six family filters and Previous/Next controls expose every case. All sources
retain their original order and text. The loader verifies pinned hashes and
replays the candidate through the same verification module on each interaction.
An integrity mismatch blocks rendering.

## Scope

The collection uses fictional research cases with one or two supplied passages
per question. Live mode can insert one additional passage. It does not run a
retriever or measure attack success rates. Recorded-mode times are historical EXP-044 measurements;
live-mode times come from the selected local round. Neither is UI timing.
Source VERIFIED is not external truth verification, and S2 has no symbolic verdict.

The [specification](SPEC.md), [M2 contract](M2_SPEC.md) and [M3 contract](M3_SPEC.md)
map the implementation to the supervisor's plan. The [M4 contract](M4_SPEC.md)
and [M5 contract](M5_SPEC.md) cover proof display and local round accounting.
The final five-passage collection, venue deployment and independent audience
validation remain separate work. See [M1 verification](../docs/arena_m1_results.md)
and [M2 checks and actual integration sample](../docs/arena_m2_results.md).

## Checks

The loader tests use the Python standard library:

```bash
python3 -B -m unittest tests.test_arena_replay -v
```

With the local server running, the browser smoke test uses an installed
Playwright module and matching Chromium executable:

```bash
TDK_PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs \
TDK_BROWSER_EXECUTABLE=/absolute/path/to/chromium \
node tests/arena_browser_check.mjs
```

`TDK_ARENA_URL` optionally changes the localhost address;
`TDK_ARENA_SCREENSHOT_DIR` optionally selects where UI screenshots are saved.
The test exercises navigation, every family, the truth/consistency distinction,
reference visibility, exact-score preservation, download and mobile layout.
It makes no model calls and writes no experimental records. The separate
`tests/arena_m2_browser_check.mjs` checks live-mode isolation with no inference
by default. Setting `TDK_ARENA_LIVE_SMOKE=1` explicitly enables one actual
three-call smoke round; this is optional and should not be run as an efficacy test.

`tests/arena_m3_browser_check.mjs` checks all six templates, free text, insertion
order and restore without inference. `TDK_ARENA_M3_SMOKE=1` enables one AI proposal
and one three-call edited round; `TDK_ARENA_M3_SCREENSHOT` sets a new screenshot
path. Do not overwrite existing smoke evidence. See [M3 report](../docs/arena_m3_results.md).

`tests/arena_m4_browser_check.mjs` checks graph rendering, source highlights,
REFUTED, CONFLICT, VERIFIED-but-wrong, extraction failure, export and page width.
It never runs inference. `TDK_ARENA_M4_SCREENSHOT_DIR` optionally selects a new
screenshot directory. See [M4 evidence](../docs/arena_m4_results.md).

M5 uses standard-library SQLite and adds `qrcode==8.2` only to the UI environment.
Update that environment from `requirements-arena.txt` after pulling these files.

```bash
python3 -B -m unittest tests.test_arena_ledger -v
python3 -B -m tests.arena_m5_acceptance
```

The acceptance script uses temporary databases, 100 explicit simulated rounds
and 20 concurrent database/admission clients; it writes a uniquely named software
report under `results/demo/arena_m5_acceptance/`. It makes no model calls.
`tests/arena_m5_browser_check.mjs` requires the archived examples imported above.
It checks UI/export/QR display and 20 simultaneous read-only browser sessions.
Use `TDK_ARENA_M5_SCREENSHOT_DIR` for new screenshots and `TDK_ARENA_M5_REPORT`
for an exclusive report file. These checks do not measure concurrent inference
throughput. See [M5 evidence and limitations](../docs/arena_m5_results.md).
