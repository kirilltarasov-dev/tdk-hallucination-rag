# Arena M4: auditable proof view

Display a provenance graph, executed-stage checklist, verdict badge and linked
source highlights from a replay-validated candidate trace. Apply the same panel
to recorded EXP-044 and live M2/M3 rounds. Do not alter extraction, guards, rules,
release policy, raw experiments, or model prompts. No inference is required.

Nodes distinguish question frame, draft claim, supplied sources, validated neural
facts, audited negative statements and final decision. Edges describe provenance
or target matching, not external truth. Show all retained facts, including
wrong-year/event facts, and sources with no validated facts. Invalid extraction
must never produce accepted fact nodes. Negative statements come only from the
recorded deterministic source audit, not invented neural facts.

Checklist statuses are derived from trace fields and the frozen control flow:
independent answer parse, extraction validation, composition, source audit,
answer audit and final decision. Source checks list only recorded iterations;
unvisited sources say NOT REACHED. A blocked source check is not a false-source
judgment. Do not pretend to have a per-rule instrumentation log: only emitted
rule IDs and executed stage outcomes are available. Display that limitation.

Highlight exact witness quotations and blocking source checks. Extractor errors
can identify a source by their exact source-ID diagnostic prefix; highlight the
whole source as diagnostic context, not as a contradicted quotation. Do not
infer an offending source when the trace does not identify one. Escape source
text and DOT labels, and fail closed on a trace/input mismatch.

Add a separate Proof examples mode. REFUTED example uses the unchanged saved
EXP-040 E040-018 S1 draft and V2 extraction, replayed through the current candidate.
Label this offline retrospective replay, not an EXP-044 result or fresh V3 run.
The M3 extraction-failure example uses its saved actual round. Verify pinned
source artifact hashes and retain provenance/raw extraction in proof exports.

Acceptance: all 24 existing traces render; correct handling of VERIFIED-but-wrong,
CONFLICT, REFUTED and early UNKNOWN; negative-source graph; wrong-target facts;
blocked/unvisited checks; tamper rejection and safe text; browser graph, verdict,
rule checklist, quotation highlights and download; M1/M2/M3 regressions without
inference. Five-passage collection and M5 audience scoring remain separate work.
