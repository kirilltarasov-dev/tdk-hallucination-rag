"""EXP-045 offline review materials and analysis of explicit AI draft labels."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import subprocess

RAW = Path('results/raw/exp044_fresh_transfer.jsonl')
FIXTURE = Path('data/synthetic/exp044_generated_transfer_cases.json')
PRIMARY = Path('results/processed/exp044_fresh_transfer_summary.json')
MANIFEST = Path('results/raw/exp044_fresh_transfer_manifest.json')
PROTOCOL = Path('docs/exp045_semantic_review_protocol.md')
PACKET = Path('results/annotation/exp045_anonymized_packet.json')
KEY = Path('results/annotation/exp045_private_mapping.json')
HUMAN = Path('results/annotation/exp045_blank_human_template.json')
READABLE = Path('deliverables/EXP045_Anonymized_Review_Packet.md')
LABELS = Path('results/annotation/exp045_assistant_labels.json')
ROWS = Path('results/processed/exp045_semantic_pairs.jsonl')
SUMMARY = Path('results/processed/exp045_semantic_summary.json')
TAG = 'exp045-labels-freeze-2026-11-18'
ARMS = ('S1', 'Original_NS', 'Candidate_NS')
VALUES = {
    'answer_status': ('CORRECT_WINNER', 'INCORRECT_WINNER', 'NEGATIVE_ONLY',
                      'EXPLICIT_REFUSAL', 'MIXED', 'UNCLEAR'),
    'false_target_claim': ('YES', 'NO', 'UNCLEAR'),
    'target_evidence': ('SUPPORTED', 'CONTRADICTED', 'CONFLICTED', 'UNSUPPORTED',
                        'NO_CLAIM', 'MIXED', 'UNCLEAR'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + '\n'


def inputs():
    if sha(RAW) != '1cee1a96ddedbebf31fc2c770efba608d8c28df4f37ee703121ce18852ce999c':
        raise ValueError('EXP-044 raw cases changed')
    if sha(PRIMARY) != '9e94ebd1ffd447aab0be8e0728defc70654f185fe81940eb19ff4e6963c875b6':
        raise ValueError('EXP-044 primary summary changed')
    if sha(MANIFEST) != '1034c741ee54a83bac6196f490908f986112a38d814c5b395fae181a3f639d7d':
        raise ValueError('EXP-044 manifest changed')
    manifest = json.loads(MANIFEST.read_text())
    if sha(FIXTURE) != manifest['source_sha256'][str(FIXTURE)]:
        raise ValueError('EXP-044 fixture changed')
    cases = json.loads(FIXTURE.read_text())['cases']
    rows = [json.loads(line) for line in RAW.read_text().splitlines()]
    if len(rows) != 24 or [r['case_id'] for r in rows] != [c['case_id'] for c in cases]:
        raise ValueError('Incomplete or reordered source cases')
    return cases, rows


def materialize():
    cases, rows = inputs()
    records = []
    for case, row in zip(cases, rows):
        by_text = {}
        for arm in ARMS:
            by_text.setdefault(row['answers'][arm], []).append(arm)
        for response, arms in by_text.items():
            records.append(({
                'question': row['question'],
                'fictional_unique_winner': case['authored_truth'],
                'documents': row['documents'], 'response': response,
            }, {'case_id': case['case_id'], 'arms': arms}))
    random.Random(45018).shuffle(records)
    public, mapping = [], []
    for index, (record, origin) in enumerate(records, start=1):
        record_id = f'R045-{index:03d}'
        public.append({'record_id': record_id, **record})
        mapping.append({'record_id': record_id, **origin})
    packet = {'experiment_id': 'EXP-045',
              'artifact_type': 'system_anonymized_review_packet',
              'reference_scope': 'Authored fictional unique winner; no external truth validation.',
              'records': public}
    key = {'experiment_id': 'EXP-045', 'artifact_type': 'private_system_mapping',
           'seed': 45018, 'source_sha256': {str(p): sha(p) for p in (RAW, FIXTURE, PRIMARY)},
           'mapping': mapping}
    blank = {'experiment_id': 'EXP-045', 'artifact_type': 'blank_human_review_template',
             'status': 'NOT_COMPLETED', 'reviewer_id': None,
             'prior_exposure_to_systems_or_AI_labels': None,
             'records': [{'record_id': r['record_id'],
                          **{field: None for field in VALUES},
                          'rationale': '', 'response_spans': [], 'context_spans': []}
                         for r in public]}
    lines = ['# EXP-045: Anonymized semantic review packet', '',
             'Use the accompanying EXP-045 codebook. The reference is an authored fictional',
             'unique winner; supplied sources can be false. Review the entire response.',
             'System identities and existing scores are withheld. Record labels in the',
             'blank human template. No annotations in this packet have been completed.', '']
    for record in public:
        lines += [f'## {record["record_id"]}', '', f'Question: {record["question"]}', '',
                  f'Fictional unique winner: {record["fictional_unique_winner"]}', '', 'Sources:', '']
        lines += [f'- {source_id}: {text}' for source_id, text in record['documents'].items()]
        lines += ['', 'Verbatim response:', '', '> ' + record['response'].replace('\n', '\n> '), '']
    return {PACKET: encoded(packet), KEY: encoded(key), HUMAN: encoded(blank),
            READABLE: '\n'.join(lines).rstrip() + '\n'}


def verify_materials():
    for path, text in materialize().items():
        if path.read_text() != text:
            raise ValueError(f'Review material differs from source replay: {path}')


def validate_labels(data, packet):
    if (data.get('reviewer_kind') != 'AI' or data.get('human_reviewed') is not False
            or data.get('blinded') is not False or data.get('external_fact_check') is not False):
        raise ValueError('This analysis accepts disclosed, non-blinded AI draft labels only')
    if data.get('packet_sha256') != sha(PACKET) or data.get('protocol_sha256') != sha(PROTOCOL):
        raise ValueError('Label packet/codebook provenance mismatch')
    public = {record['record_id']: record for record in packet['records']}
    labels = data.get('records', [])
    if len(labels) != len(public) or {r['record_id'] for r in labels} != set(public):
        raise ValueError('Missing, duplicate or extra review record')
    result = {}
    for label in labels:
        record = public[label['record_id']]
        for field, values in VALUES.items():
            if label.get(field) not in values:
                raise ValueError(f'Invalid {field} for {label["record_id"]}')
        if not isinstance(label.get('rationale'), str) or not label['rationale'].strip():
            raise ValueError('Missing rationale')
        spans = label.get('response_spans', [])
        if not spans or any(not span or span not in record['response'] for span in spans):
            raise ValueError('Invalid verbatim response quotation')
        for span in label.get('context_spans', []):
            if (set(span) != {'doc_id', 'quote'} or span['doc_id'] not in record['documents']
                    or not span['quote'] or span['quote'] not in record['documents'][span['doc_id']]):
                raise ValueError('Invalid source quotation')
        if label['answer_status'] == 'EXPLICIT_REFUSAL' and (
                label['false_target_claim'] != 'NO' or label['target_evidence'] != 'NO_CLAIM'):
            raise ValueError('Pure refusal cannot assert a target fact')
        result[label['record_id']] = label
    return result


def analyze():
    verify_materials()
    packet = json.loads(PACKET.read_text())
    labels = validate_labels(json.loads(LABELS.read_text()), packet)
    mapping = json.loads(KEY.read_text())['mapping']
    assigned = {}
    for entry in mapping:
        for arm in entry['arms']:
            identity = (entry['case_id'], arm)
            if identity in assigned:
                raise ValueError('Duplicate arm mapping')
            assigned[identity] = labels[entry['record_id']]
    cases, original = inputs()
    rows = [{'case_id': case['case_id'], 'family': case['family'],
             'provenance': 'unvalidated_nonblinded_AI_assessment',
             'human_reviewed': False,
             'original_exact_scores': raw['scores'],
             **{arm: assigned[(case['case_id'], arm)] for arm in ARMS}}
            for case, raw in zip(cases, original)]
    counts = {arm: {field: {value: sum(r[arm][field] == value for r in rows)
                            for value in values} for field, values in VALUES.items()}
              for arm in ARMS}
    comparisons = {}
    for base in ('S1', 'Original_NS'):
        complete = [r for r in rows if all(r[a]['false_target_claim'] != 'UNCLEAR'
                                           for a in (base, 'Candidate_NS'))]
        removed = [r['case_id'] for r in complete if r[base]['false_target_claim'] == 'YES'
                   and r['Candidate_NS']['false_target_claim'] == 'NO']
        introduced = [r['case_id'] for r in complete if r[base]['false_target_claim'] == 'NO'
                      and r['Candidate_NS']['false_target_claim'] == 'YES']
        comparisons[base] = {'complete_pairs': len(complete),
                             'removed_AI_false_target_claim_labels': removed,
                             'introduced_AI_false_target_claim_labels': introduced,
                             'answer_status_transitions': dict(Counter(
                                 r[base]['answer_status'] + ' -> ' + r['Candidate_NS']['answer_status']
                                 for r in rows))}
    summary = {
        'experiment_id': 'EXP-045', 'status': 'completed_exploratory_AI_only_review',
        'question_count': len(rows), 'distinct_review_records': len(labels),
        'arm_outputs': len(rows) * len(ARMS), 'new_inference_calls': 0,
        'human_reviewed_records': 0, 'AI_reviewer_blinded': False,
        'source_sha256': {str(p): sha(p) for p in
                          (RAW, FIXTURE, PRIMARY, PROTOCOL, PACKET, KEY, LABELS,
                           Path('experiments/exp045_semantic_review.py'))},
        'counts': counts, 'candidate_paired_comparisons': comparisons,
        'originally_unscorable_S1': [r for r in rows
                                    if r['original_exact_scores']['S1']['category'] == 'UNSCORABLE'],
        'false_claim_and_supported_source': {
            arm: sum(r[arm]['false_target_claim'] == 'YES'
                     and r[arm]['target_evidence'] == 'SUPPORTED' for r in rows) for arm in ARMS},
        'limitations': ['Post-hoc labels by the development assistant; no independent human validation.',
                       'Fictional unique-winner reference, not externally checked world facts.',
                       'Target propositions only; not a comprehensive free-text factuality score.',
                       'EXP-044 primary scoring and INCONCLUSIVE result remain unchanged.',
                       'Repeated authored families and shared outputs; no population inference.'],
    }
    return {SUMMARY: encoded(summary),
            ROWS: ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows)}


def write_exclusive(payloads):
    if any(path.exists() for path in payloads):
        raise FileExistsError('Artifacts exist; do not overwrite or silently continue')
    for path, content in payloads.items():
        with path.open('x', encoding='utf-8') as handle:
            handle.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--prepare', action='store_true')
    modes.add_argument('--analyze', action='store_true')
    modes.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        write_exclusive(materialize())
        print('Anonymized packet, private key and blank human materials saved.')
    elif args.analyze:
        paths = [str(p) for p in (PROTOCOL, PACKET, KEY, LABELS, Path('experiments/exp045_semantic_review.py'))]
        subprocess.run(['git', 'ls-files', '--error-unmatch', '--', *paths],
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run(['git', 'diff', '--exit-code', TAG, '--', *paths],
                       check=True, stdout=subprocess.DEVNULL)
        write_exclusive(analyze())
        print('AI-only descriptive results saved; human-reviewed records: 0.')
    elif args.check:
        for path, text in analyze().items():
            if path.read_text() != text:
                raise ValueError(f'Analysis replay mismatch: {path}')
        print('Packet, labels, sources and derived analysis replay verified.')
    else:
        cases, _ = inputs()
        print(f'EXP-045: {len(cases)} questions; no model calls; use --prepare or --check.')


if __name__ == '__main__':
    main()
