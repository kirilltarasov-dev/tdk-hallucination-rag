# Arena M5: persisted rounds, accounting and audience entry

This is software acceptance, not an efficacy experiment. Use SQLite WAL with
short atomic transactions and a busy timeout. Store immutable completed records,
raw payloads and SHA-256 digests; keep failed/interrupted attempts separately.
The existing unique raw-call directories remain authoritative. A repeated run ID
with identical content is idempotent; different content under that ID is rejected.

Post-generation scores use the frozen scorer and canonical challenge reference.
Never send references, scoreboard metadata or participant IDs to inference.
Count CORRECT, WRONG, ABSTAIN and UNSCORABLE separately per system and attack
origin. Unknown source verdicts are not scored as attack resistance. AI proposal
calls do not become three-system evaluation rounds. No attack success rate or
causal effect is estimated from self-selected, repeated demonstration questions.

Live, archived demonstration and explicitly simulated software records are
separate populations in storage, views and JSONL exports. Existing archived
rounds may be imported by an explicit local maintenance command; no automatic
research-data import or background inference occurs. The exported round includes
its inputs, exact scores, attack provenance, raw call payload and origin.

Both AI proposals and evaluation use admission control before invoking the worker:
6 accepted requests per anonymous session per 10 minutes, 30 globally per hour,
one active request with a 240-second lease. Admission is atomic. The existing
worker file lock remains the final local inference exclusion mechanism. A client
worker timeout is 180 seconds. Rejections, failures and expired leases retain
explicit attempt records; no silent retry occurs. Anonymous session IDs are not
authentication and can be reset; this is a local/supervised demonstration policy.

Provide an audience-entry link and QR. Default localhost is explicitly usable
only on the host. An organizer may configure a reachable HTTP(S) URL; do not
publish or change network binding automatically. QR display is not evidence of
phone/network reachability. Display a local demo scoreboard with manual refresh
and export. Deployment and independent audience validation remain separate work.

Acceptance: 100 simulated rounds with exact expected category/attack counts;
20 simultaneous database clients without lost/duplicated records; 20 simultaneous
admission attempts with exactly one accepted request; failures, timeout expiry,
rate limits, tampering and idempotence; UI empty/populated/filtered/export states;
20 browser sessions on read-only scoreboard; QR round-trip decoding; M1–M4
regression. Tests use temporary SQLite files and explicit software provenance,
never fabricated model observations or claimed 20-user inference throughput.
