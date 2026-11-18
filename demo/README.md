# RAG Red-Team Arena

The Arena offers a recorded explorer (M1) and explicit local generation (M2).
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
per question. It does not run a retriever, accept attack edits or measure attack
success rates. Recorded-mode times are historical EXP-044 measurements;
live-mode times come from the selected local round. Neither is UI timing.
Source VERIFIED is not external truth verification, and S2 has no symbolic verdict.

The [specification](SPEC.md) and [M2 contract](M2_SPEC.md) map the implementation
to the supervisor's plan. Five-passage challenges, attack editor, complete proof
graph and audience scoreboard remain future work. See [M1 verification](../docs/arena_m1_results.md)
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
