"""Derive descriptive diagnostics and a figure from a completed frozen run.

This is presentation and failure inspection, not a replacement primary scorer.
Run the frozen experiments.exp046_evaluation --check before using its outputs.
No model imports, inference, retrospective semantic labels or hypothesis tuning.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path


def load_completed():
    complete = json.loads(Path('results/raw/exp046/complete.json').read_text())
    for name, expected in complete['sha256'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Completed artifact changed: {name}')
    summary = json.loads(Path('results/processed/exp046_summary.json').read_text())
    rows = [json.loads(s) for s in Path('results/raw/exp046/cases.jsonl').read_text().splitlines()]
    cases = json.loads(Path('data/synthetic/exp046_five_passage_cases.json').read_text())['cases']
    if len(rows) != 240 or summary['unique_model_calls'] != 720:
        raise ValueError('Complete frozen run required')
    if [r['case_id'] for r in rows] != [c['case_id'] for c in cases]:
        raise ValueError('Fixture/row ordering differs')
    return summary, cases, rows


def inspect_failures(cases, rows):
    families = list(dict.fromkeys(c['family'] for c in cases))
    result = {'scope': 'Descriptive inspection of frozen automatic decisions; no semantic relabelling.',
              'by_family': {}, 'first_case_for_each_rule': {}}
    for family in families:
        group = [r for c, r in zip(cases, rows) if c['family'] == family]
        result['by_family'][family] = {
            'n': len(group),
            'verdicts': dict(Counter(r['verification']['decision']['verdict'] for r in group)),
            'decision_rules': dict(Counter(r['verification']['decision']['rule_id'] for r in group)),
            'withheld_S1_categories': dict(Counter(r['scores']['S1']['category'] for r in group if r['action'] == 'ABSTAIN')),
            'validation_errors': dict(Counter(r['verification']['validation_error'] for r in group if r['verification']['validation_error'])),
            'V3_at_cap': sum(r['calls']['V3']['output_tokens'] == 1024 for r in group),
        }
    for r in rows:
        rule = r['verification']['decision']['rule_id']
        result['first_case_for_each_rule'].setdefault(rule, r['case_id'])
    result['selection_rule'] = 'First occurrence in frozen execution order per decision rule; illustrative only.'
    result['input_sha256'] = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (Path('results/raw/exp046/cases.jsonl'), Path('results/processed/exp046_summary.json'))}
    return result


def figure(summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(2, 1, figsize=(7.5, 4.3), gridspec_kw={'height_ratios': [1.5, 1]})
    fig.subplots_adjust(left=.27, right=.95, top=.91, bottom=.14, hspace=.95)
    ax = axes[0]
    bounds = summary['primary_paired_utility_bounds']
    envelope = summary['stratified_bootstrap_95pct_sensitivity_envelope']
    for y, values, color, width in [(1, bounds, '#254e70', 6), (0, envelope, '#66717e', 2)]:
        ax.hlines(y, *values, color=color, linewidth=width)
        ax.vlines(values, y-.12, y+.12, color=color, linewidth=1.5)
        if values[0] == values[1]:
            ax.plot(values[0], y, '|', color=color, markersize=14)
        ax.text(values[0], y+.20, f'{values[0]:+.3f}', ha='center', fontsize=9)
        if values[0] != values[1]:
            ax.text(values[1], y+.20, f'{values[1]:+.3f}', ha='center', fontsize=9)
    ax.axvline(0, color='#555555', linestyle='--', linewidth=1)
    ax.set(yticks=[1, 0], yticklabels=['Full-N utility bounds', 'Bootstrap envelope'], ylim=(-.4, 1.5),
           xlim=(min(-.05, min(envelope)-.06), max(.05, max(envelope)+.06)),
           xlabel='Candidate NS minus S1 utility per question')
    ax.set_title('Restricted automatic evaluation on 240 authored questions', fontsize=11, pad=13)
    ax = axes[1]
    retention = summary['correct_draft_retention']
    interval = summary['retention_wilson_95pct_descriptive']
    if retention is not None:
        ax.hlines(0, *interval, color='#254e70', linewidth=2)
        ax.plot(retention, 0, 'o', color='#254e70', markersize=6)
        ax.text(retention, .22, f'{summary["retained_correct"]}/{summary["S1_correct_denominator"]} = {retention:.1%}', ha='center', fontsize=10)
    else:
        ax.text(.5, 0, 'Undefined: no correct S1 draft', ha='center')
    ax.axvline(.8, color='#555555', linestyle='--', linewidth=1)
    ax.text(.8, -.32, '80% point threshold', ha='center', fontsize=8)
    ax.set(yticks=[0], yticklabels=['Correct-draft retention'], xlim=(0, 1.03), ylim=(-.42, .48),
           xlabel='Retained fraction with descriptive 95% Wilson interval')
    for ax in axes:
        for side in ('top', 'right', 'left'): ax.spines[side].set_visible(False)
        ax.tick_params(axis='y', length=0)
    for extension in ('png', 'svg'):
        fig.savefig(f'results/figures/exp046_primary_bounds.{extension}', dpi=250, facecolor='white')
    plt.close(fig)


def write_report(s, diagnostics):
    arms = ('S1', 'S2', 'Candidate_NS')
    cats = ('CORRECT', 'WRONG', 'ABSTAIN', 'UNSCORABLE')
    fmt = lambda x: f'[{x[0]:+.6f}, {x[1]:+.6f}]'
    transitions = s['paired_category_transitions_from_S1']['Candidate_NS']
    withheld_wrong = transitions.get('WRONG -> ABSTAIN', 0)
    withheld_correct = transitions.get('CORRECT -> ABSTAIN', 0)
    withheld_unknown = transitions.get('UNSCORABLE -> ABSTAIN', 0)
    lines = [
        '# EXP-046 Frozen five-passage evaluation', '',
        'Completed on 2026-11-26 after explicit author approval. All 240 authored',
        'questions and 720 local model calls completed with the method frozen at',
        '`8bb0d0f0aece395ab8903b4afc83553ebfc63ba8`, tag',
        '`exp046-freeze-2026-11-18`. No case was replaced and no prompt, rule or',
        'scorer was changed. Laptop sleep occurred, but the original process',
        'continued without a runner restart or replay of completed calls.', '',
        '## Primary result', '',
        f'**Predeclared screen: {s["screen"]}.**', '',
        f'- Full-N candidate-minus-S1 utility identification bounds: **{fmt(s["primary_paired_utility_bounds"])}**.',
        f'- Stratified bootstrap sensitivity envelope: **{fmt(s["stratified_bootstrap_95pct_sensitivity_envelope"])}**.',
        f'- Correct S1 drafts retained: **{s["retained_correct"]}/{s["S1_correct_denominator"]}**.',
        f'- Correct-draft retention: **{s["correct_draft_retention"]:.6f}**.' if s['correct_draft_retention'] is not None else '- Correct-draft retention is undefined: no correct S1 draft.',
        f'- Descriptive 95% Wilson retention interval: {fmt(s["retention_wilson_95pct_descriptive"])}.' if s['retention_wilson_95pct_descriptive'] else '- No Wilson interval is defined.', '',
        'The criterion jointly requires a positive identification lower endpoint,',
        'a positive bootstrap lower endpoint and at least 80% point retention.',
        'The bootstrap resamples paired questions within each of the six fixed',
        'families (10,000 resamples, seed 46019, nearest-rank percentiles). It is',
        'conditional sensitivity for this authored mixture, not a population or',
        'human-validated hallucination interval. N=240 was a practical allocation,',
        'not a claim of adequate power for a small effect.', '',
        f'The policy withheld **{withheld_wrong} scored wrong drafts**, **{withheld_correct} correct drafts**',
        f'and **{withheld_unknown} unscorable drafts**. The known contribution to the paired',
        f'utility sum is {withheld_wrong}-{withheld_correct}={withheld_wrong-withheld_correct}; the withheld unknown',
        f'drafts contribute [{-withheld_unknown}, +{withheld_unknown}] before division by 240.', '',
        '| Outcome, n=240 | S1 | S2 | Candidate NS |',
        '|---|---:|---:|---:|']
    for c in cats:
        lines.append('| '+c+' | '+' | '.join(str(s['metrics'][a]['counts'][c]) for a in arms)+' |')
    lines += ['| Utility bounds | '+' | '.join(fmt(s['metrics'][a]['mean_utility_bounds']) for a in arms)+' |',
              '| Coverage bounds | '+' | '.join(fmt(s['metrics'][a]['answer_coverage_bounds']) for a in arms)+' |',
              '| False abstentions / 120 unambiguous true-evidence cases | '+' | '.join(str(s['metrics'][a]['false_abstentions']) for a in arms)+' |', '',
              'CORRECT, WRONG and the canonical ABSTAIN retain utilities +1, -1 and 0.',
              'UNSCORABLE outputs remain unknown in [-1,+1]; they are not retrospectively',
              'converted to errors, abstentions or semantic successes. Identical released',
              'strings cancel exactly in the paired difference. Historical experiments',
              'retain their original primary scoring and interpretations.', '',
              '## Family diagnostics', '',
              '| Family, n=40 | S1 C/W/A/U | S2 C/W/A/U | Candidate C/W/A/U |',
              '|---|---|---|---|']
    families = ('clean', 'paraphrase', 'negated_distractor', 'conflict', 'no_target_evidence', 'false_source_only')
    for f in families:
        lines.append('| '+f+' | '+' | '.join('/'.join(str(s['by_family'][f][a]['counts'][c]) for c in cats) for a in arms)+' |')
    lines += ['', f'Candidate verdict counts: `{json.dumps(s["candidate_verdicts"], sort_keys=True)}`.',
              f'Original-extraction validation failures: **{s["candidate_extraction_validation_failures"]}**.',
              f'V3 outputs at the 1,024-token cap: **{s["at_token_cap_by_stage"]["V3"]}**.',
              f'False-source-control releases: **{s["candidate_false_source_releases"]}/40**.', '',
              'A false-source release is agreement with supplied evidence, not a test of',
              'source credibility. UNKNOWN may arise from extraction or supported-language',
              'limitations and must not be described as a successful symbolic refutation.',
              'See `results/processed/exp046_diagnostics.json` for per-family decision rules,',
              'validation errors and the S1 categories withheld. Its illustrative case IDs',
              'use the first occurrence of each rule in the frozen execution order. These',
              'are descriptive diagnostics, not independent semantic annotation.', '',
              '## Paired transitions and secondary comparisons', '',
              'Candidate transitions from S1:', '', '```json',
              json.dumps(s['paired_category_transitions_from_S1']['Candidate_NS'], indent=2, sort_keys=True), '```', '',
              f'S2 minus S1 utility bounds: {fmt(s["secondary_descriptive_paired_bounds"]["S2_minus_S1"])}.',
              f'Candidate minus S2 utility bounds: {fmt(s["secondary_descriptive_paired_bounds"]["Candidate_NS_minus_S2"])}.', '',
              'S2 is secondary same-model review, not an independent judge. These comparisons',
              'cannot replace the sole primary screen. A release-only policy cannot introduce',
              'a new assertion, so wrong-answer nonincrease alone does not demonstrate benefit.', '',
              '## Workload and execution conditions', '',
              f'There were **{s["unique_model_calls"]}** unique calls, **{s["unique_input_tokens"]:,}** input tokens',
              f'and **{s["unique_output_tokens"]:,}** generated tokens, within the 307,200-token cap.',
              f'Summed recorded unique model-call time was {s["summed_unique_model_call_seconds"]:.3f} seconds;',
              f'model loading took {s["model_load_seconds"]:.3f} seconds.',
              f'Peak MLX process allocation was {s["peak_MLX_process_memory_GB"]:.3f} GB.', '',
              '| Arm | Mean s/question | p50 | p95 | Calls/question | Input tokens | Output tokens |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for a in arms:
        c = s['cost'][a];l = c['latency_seconds']
        lines.append(f'| {a} | {l["mean"]:.3f} | {l["p50"]:.3f} | {l["p95_nearest_rank"]:.3f} | {c["calls_per_question"]} | {c["input_tokens"]} | {c["output_tokens"]} |')
    lines += ['', 'The draft call is shared: do not sum these arm costs to estimate actual total',
              'work. Per-arm latency includes the draft, and the candidate also includes rule',
              'execution. Peak MLX allocation is process-wide, not isolated per-arm memory.',
              'Laptop sleep/dark-wake cycles and concurrent document/desktop work occurred.',
              'See `docs/exp046_execution_notes.md`. Preserve original timers and outliers;',
              'these measurements are execution telemetry, not an isolated latency benchmark.',
              'No compute saving or cross-run speed comparison is established.', '',
              '## Reproducibility and interpretation limits', '',
              'The frozen raw-to-summary replay passed without inference:', '',
              '```sh', '.venv/bin/python -B -m experiments.exp046_evaluation --check', '```', '',
              '- Raw artifacts: `results/raw/exp046/{manifest,cases,calls,attempts,complete}` with `.json` or `.jsonl` extensions.',
              '- Primary processed summary: `results/processed/exp046_summary.json`.',
              '- Supplementary diagnostics and figure: `docs/report_exp046.py`.',
              '- Protocol and preparation: `docs/exp046_proposed_protocol.md` and `docs/exp046_preparation.md`.', '',
              'The developer-authored task uses six familiar mechanism templates and supplied',
              'short controlled-language statements. Fresh names and more cases do not',
              'establish broad domain generalization. The source guard recognizes the sentence',
              'grammar itself, and no rule-only baseline was included; the necessity or value',
              'of the neural extraction stage is therefore not established. Individual component',
              'effects, a real retriever, natural scientific text and source credibility remain',
              'outside the measured scope. No independent human labels are available. This is',
              'an output-contract utility study, not a validated hallucination-rate study.', '',
              'This evaluation completes whether its screen passes, fails or is inconclusive.',
              'Do not tune on its outputs, change labels, drop false-source controls or enlarge',
              'the sample after seeing the result. Any method correction requires a separately',
              'documented development decision and a new experiment identifier.', '']
    with Path('docs/exp046_results.md').open('x') as handle:
        handle.write('\n'.join(lines))


if __name__ == '__main__':
    summary, cases, rows = load_completed()
    target = Path('results/processed/exp046_diagnostics.json')
    with target.open('x') as f:
        diagnostics = inspect_failures(cases, rows)
        json.dump(diagnostics, f, indent=2)
        f.write('\n')
    figure(summary)
    write_report(summary, diagnostics)
