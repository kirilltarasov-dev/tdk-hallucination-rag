# EXP-046 execution conditions

The author authorized the previously described 240-case, 720-call bounded run
on 2026-11-26. The existing freeze passed verification before execution. The
process started at 13:06:26 UTC from commit
`8bb0d0f0aece395ab8903b4afc83553ebfc63ba8` with offline cached weights.
The authorization text and hardware/runtime metadata are preserved in
`results/raw/exp046/manifest.json`.

During execution, the author needed to close the laptop while travelling to
class. At the last check before that interruption, 25 complete cases and 76
complete calls were saved. On returning, the same operating-system process
(PID 75461 in this session) remained present: 59 cases and 178 calls were saved,
and the log then advanced to 60 cases / 180 calls. No runner restart, retry,
case replacement, code change or resumption from partial logs was performed.
macOS power logs also contained sleep/dark-wake events during this interval.
The inspected log records clamshell sleep at 14:12:33 CET and a return to full
wake at 14:22:17 CET on 2026-11-26, with intermediate dark-wake cycles. These
timestamps describe operating-system power states, not a measured duration of
inference suspension and not a correction to individual call timings.

Document rendering and other ordinary desktop activity occurred on the same
machine while inference was running. The per-call timer uses
`time.perf_counter`; its behavior over sleep is platform-dependent. Preserve
all original timings without deleting outliers or subtracting an estimated
sleep duration. Report measured latency as execution telemetry under these
conditions, not as an isolated speed benchmark or evidence of compute savings.
Token and call counts remain the directly recorded workload measures. Final
run completion and result interpretation belong in `docs/exp046_results.md`
only after the full raw-to-summary replay passes.
