"""Post-run diagnostics and figures; never changes frozen EXP-040 scoring."""
from collections import Counter
import hashlib
import json
from pathlib import Path

DATA = Path('data/synthetic/exp040_generated_answer_cases.json')
RAW = Path('results/raw/exp040_generated_answers.jsonl')
CALLS = Path('results/raw/exp040_model_calls.jsonl')
SUMMARY = Path('results/processed/exp040_generated_answers_summary.json')
REPORT = Path('results/processed/exp040_case_diagnostics.json')
FIGURE = Path('results/figures/exp040_generated_answer_outcomes')


def diagnostics():
    summary = json.loads(SUMMARY.read_text())
    if hashlib.sha256(RAW.read_bytes()).hexdigest() != summary['raw_sha256']:
        raise ValueError('Raw results changed')
    if hashlib.sha256(CALLS.read_bytes()).hexdigest() != summary['calls_sha256']:
        raise ValueError('Call log changed')
    cases = {c['case_id']: c for c in json.loads(DATA.read_text())['cases']}
    rows = [json.loads(line) for line in RAW.read_text().splitlines()]
    calls = [json.loads(line) for line in CALLS.read_text().splitlines()]
    if len(rows) != 40 or len(calls) != 120:
        raise ValueError('Expected complete run')
    removed, lost, self_review_damage, false_released = [], [], [], []
    details = []
    for row in rows:
        case = cases[row['case_id']]
        a, b, c = (row['scores'][s]['category'] for s in ('S1','S2','NS'))
        item = {'case_id': row['case_id'], 'family': case['family'],
                'question': case['question'], 'authored_truth': case['authored_truth'],
                'answers': row['answers'], 'categories': {'S1':a,'S2':b,'NS':c},
                'final_rule': row['policy']['decision']['rule_id'],
                'validation_error': row['verification']['validation_error']}
        details.append(item)
        if a == 'WRONG' and c == 'ABSTAIN': removed.append(item)
        if a == 'CORRECT' and c == 'ABSTAIN': lost.append(item)
        if a == 'ABSTAIN' and b == 'WRONG': self_review_damage.append(item)
        if c == 'WRONG': false_released.append(item)
    return {'experiment_id': 'EXP-040', 'analysis': 'post-run descriptive trace inspection; original scores unchanged',
            'source_sha256': {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (DATA,RAW,CALLS,SUMMARY)},
            'lost_correct_answers_by_family': dict(Counter(r['family'] for r in lost)),
            'removed_wrong_answers_by_family': dict(Counter(r['family'] for r in removed)),
            'lost_correct_answers': lost, 'removed_wrong_answers': removed,
            'self_review_abstention_to_wrong': self_review_damage, 'false_answers_released': false_released,
            'strict_name_match_caveat_ids': ['E040-018','E040-019'],
            'strict_name_match_caveat': 'Velvet Otters omits the numeric suffix of the authored entity; these are protocol mismatches, not externally established factual hallucinations.',
            'unique_call_totals': {'calls':len(calls), 'input_tokens':sum(r['input_tokens'] for r in calls),
                                   'output_tokens':sum(r['output_tokens'] for r in calls),
                                   'summed_model_call_seconds':sum(r['latency_seconds'] for r in calls),
                                   'model_load_seconds':calls[0]['model_load_seconds'],
                                   'finish_reasons':dict(Counter(r['finish_reason'] for r in calls))},
            'case_results':details}


def main():
    report = diagnostics()
    with REPORT.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
    if any(FIGURE.with_suffix(ext).exists() for ext in ('.png','.svg')):
        raise FileExistsError('Figure exists; no overwrite')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    summary = json.loads(SUMMARY.read_text())
    fig, ax = plt.subplots(figsize=(9.2,4.6), layout='constrained')
    bottom = [0,0,0]
    labels = ['S1-style\nGenerated draft', 'S2-style\nSame-model review', 'NS-release\nVerify or abstain']
    for category, title, color in [('CORRECT','Correct under fixed scorer','#0072B2'),
                                   ('WRONG','Wrong under fixed scorer','#D55E00'),
                                   ('ABSTAIN','Abstain','#CCCCCC')]:
        values = [summary['metrics'][s]['counts'][category] for s in ('S1','S2','NS')]
        ax.bar(range(3),values,bottom=bottom,label=title,color=color,width=.62)
        for i,v in enumerate(values):
            if v: ax.text(i,bottom[i]+v/2,str(v),ha='center',va='center',weight='bold',
                          color='black' if category=='ABSTAIN' else 'white',fontsize=12)
        bottom = [a+b for a,b in zip(bottom,values)]
    ax.set_xticks(range(3),labels)
    ax.set_ylim(0,43)
    ax.set_ylabel('Questions (40 authored fictional cases)')
    ax.set_title('EXP-040: Fewer scored errors, but too many correct answers withheld',loc='left',pad=18)
    ax.spines[['top','right']].set_visible(False)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.17),ncol=3,frameon=False,fontsize=8.5)
    fig.suptitle('Correct-answer retention: 17/25 = 68% (target 80%); feasibility screen failed',
                 fontsize=10,x=.08,ha='left')
    for ext in ('.png','.svg'): fig.savefig(FIGURE.with_suffix(ext),dpi=180,bbox_inches='tight')
    plt.close(fig)
    print(json.dumps({k:report[k] for k in ('lost_correct_answers_by_family','removed_wrong_answers_by_family','unique_call_totals')},indent=2))


if __name__ == '__main__':
    main()
