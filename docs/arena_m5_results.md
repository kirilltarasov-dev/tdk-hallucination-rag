# Arena M5: persisted rounds and local audience controls

**Date:** 2026-11-18. **Status:** implemented with local software acceptance
within `demo/M5_SPEC.md`. No new model calls or efficacy experiments were run.
This does not establish venue readiness or concurrent inference throughput.

## Delivered behavior

SQLite WAL stores admissions, completed round payloads and integrity digests.
Writes use short atomic transactions with a busy timeout. Completed run IDs are
idempotent: identical repeated writes do not count twice; different content is
rejected. Raw worker directories remain unchanged and authoritative. Failures,
rejections and expired admission leases remain separate attempt records.

The service validates canonical challenge metadata and attack provenance before
inference. The reference remains outside worker inputs and is used only for
post-generation scoring. Both evaluation and AI-proposal buttons use admission
control: six accepted requests per anonymous session per ten minutes, thirty
globally per hour and one active request. The 240-second lease outlasts the
180-second worker timeout; expired RUNNING attempts become INTERRUPTED on a later
admission. The existing worker lock still excludes concurrent inference. An
unavailable ledger blocks a new UI request before the worker starts. A failure
after generation preserves raw logs and does not trigger a retry.

The Round ledger screen groups exact counts by system and attack origin, with
CORRECT, WRONG, ABSTAIN and UNSCORABLE separate. AI proposals and infrastructure
failures are not answer outcomes. Live demonstrations, imported archive examples
and explicit software simulations have separate views and exports. No ASR,
causal intervention effect or hallucination reduction is inferred from these
self-selected repeated cases. The table and JSONL export use one SQLite snapshot.
The table's attack filter does not restrict the full-population export.

Two existing evaluation rounds and one existing AI proposal were explicitly
imported from verified M2/M3 archives. They appear only under Archived demo
examples. Re-importing is idempotent. Their ledger creation time is import time;
original generation provenance remains in the archived manifests. No simulated
records were added to the working app database.

The entry section provides a link and QR. The default is localhost and explicitly
works only on this host. TDK_ARENA_PUBLIC_URL changes the link/QR, not server
binding or deployment. Anonymous session IDs are not authenticated identities.
The global quota remains even if a visitor resets a session. This is intended
for a local/supervised demonstration, not an authenticated public service.

## Verification and evidence

All **154 Python tests passed**, including ten M5 tests. Tests cover:

- 100 explicitly simulated rounds written by 20 simultaneous database clients:
  exactly 100 records, 300 system outcomes, expected category/attack counts and
  100 duplicate writes ignored.
- 20 simultaneous admission attempts: exactly one accepted, nineteen denied.
- Per-session/global quotas, expired leases, failures excluded from answer counts,
  different-content duplicate rejection and stored-payload integrity checks.
- Canonical reference/base-context validation, no reference in worker arguments,
  post-generation score storage, archival imports and origin isolation.
- A database outage preventing worker invocation, and entry-URL validation.

The storage stress deliberately provisions simulated admissions in a temporary
database before concurrent writes. It does not bypass a live inference gate or
claim that 100 model requests ran. The separate admission stress exercises the
actual single-request gate. Test-double responses are marked SOFTWARE SIMULATION.
Temporary test databases are discarded; the fixture code and software reports
remain reproducible. No simulated outputs enter research results or the live app.

The M5 browser check passed empty/live and populated/archive views, exact counts,
attack filtering, full JSONL export, simulation isolation and entry QR display.
Twenty independent browser contexts simultaneously opened and read the local
ledger without UI exceptions. This tests concurrent reading sessions, not
20 concurrent generations, real audience behavior or network capacity. The raw
run-directory inventory remained unchanged. All M1–M4 browser regressions also
passed without inference.

The initial browser check exposed dropdown-selection timing after scrolling and
export. Downloads now avoid an unnecessary Streamlit rerun. The browser test
explicitly scrolls to and searches the option before selecting it, then asserts
the selected value. No model call occurred in failed checks.

The actual browser-rendered QR screenshot was decoded using zxing-cpp 2.3.0 and
returned exactly `http://127.0.0.1:8501`. This verifies encoded content, not phone
reachability. qrcode 8.2 is pinned in the separate UI environment; zxing-cpp was
used only from a temporary validation directory. The inference environment is
unchanged and the UI dependency check passes.

Final software evidence is in:
`results/demo/arena_m5_acceptance/888e89d1f87741dfaea45649fea212d0/`:

- `report.json`: 100-round accounting, concurrent storage/admission checks and
  hashes of the tested source files.
- `browser.json`: UI and twenty-session read acceptance, explicitly zero calls.
- `qr_check.json`: decoded entry URL and browser screenshot hash.

An earlier successful storage/admission report remains in the adjacent
`7d93f5066f364f1490b084ade2eccf7f/` directory; it predates additional service outage
handling and is not the final source snapshot. Neither report is an experiment.

`results/figures/arena_m5_ledger.png` was visually inspected; it clearly labels
archived examples and shows two evaluation rounds plus one proposal.
`results/figures/arena_m5_entry_qr.png` is the decoded browser QR image.

## Limits and remaining work

M1–M5 now have implementations and local acceptance evidence within their
specifications. The final five-passage challenge collection, venue deployment,
phone/network checks, supervised audience run and demo video remain open. The
original broad Arena task remains Partial. No claim of complete public-event
readiness is made from local software tests.

Independent scientific evaluation, human review, the title/scope decision,
controlled attack measurement and manuscript revision remain separate work.
Completion of the demo milestones does not establish the thesis hypothesis or
justify a new overall thesis-completion percentage.
