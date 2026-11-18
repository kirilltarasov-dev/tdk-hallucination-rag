# RAG Red-Team Arena recorded explorer

The first Arena milestone is a working local Streamlit app for the 24 saved
EXP-044 cases. It compares Standard RAG draft, Original NS and Candidate NS,
shows their supplied sources and recorded answers, and exposes the candidate's
actual rule trace. Original NS is not S2 self-verification.

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
not required to run this recorded explorer.

## A two-minute walkthrough

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

This is recorded replay of fictional research cases, with one or two supplied
passages per question. It does not run a retriever, generate new answers,
accept attack edits or measure attack success rates. The displayed times and
tokens are historical model measurements; they are not UI timing. Source
VERIFIED is not external truth verification.

The [specification](SPEC.md) maps the remaining M2–M5 work to the supervisor's
plan. In particular, the live Standard RAG/S2/NS comparison, five-passage
challenges, attack editor, complete proof graph and audience scoreboard remain
future milestones. See [M1 verification](../docs/arena_m1_results.md).

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
It makes no model calls and writes no experimental records.
