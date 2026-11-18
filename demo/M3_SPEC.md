# Arena M3: source attack editor

This is a software milestone, not an efficacy experiment. Frozen research
fixtures and the NS method remain unchanged. Live mode permits one inserted
passage per round; base passages are retained in their original order. Users
choose any insertion position, edit free text, restore the base context, or
start from six deterministic templates: date shift, ordinal swap, entity swap,
contradicting number, fake correction notice, and similar-topic distractor.
Templates use the question and visible sources only. They are illustrative
adversarial proposals, not validated attacks or new ground truth.

An optional AI attacker makes one explicit cached greedy Mistral call (256
output tokens). It sees only the question and visible base sources. Its output
fills the editor without starting evaluation. The next separate Run action
performs the existing three calls. Generation and evaluation share the local
nonblocking inference lock. Each has an exclusive raw-log directory. Failed
calls are retained, without automatic retry. No model call occurs on editing.

The displayed context is the current editor value, not a hidden pending form.
Changing text or position changes its ordered-input hash and hides mismatched
answers. An empty enabled passage blocks evaluation. Run provenance records
base context, attack type, inserted text, source ID and position, plus optional
AI proposal run ID. It is saved separately from the unchanged inference result
and included in the downloaded case. References remain post-generation only.

Acceptance: six template cases; insertion/order/bounds; no reference fields;
AI request/prompt replay and corruption checks; stale-context rejection;
exclusive provenance storage; browser template/edit/reset/isolation checks;
M1/M2 regression. Actual AI and evaluation smoke, if run, must be separately
identified as engineering evidence. Test doubles never count as observations.

Limits: numeric/ordinal/correction language can exceed the finite winner
verification grammar. UNKNOWN is not attack resistance. The legacy base cases
have 1–2 passages; the planned five-passage collection is still separate work.
No attack success rate, scoreboard, human study, or efficacy claim is introduced.
