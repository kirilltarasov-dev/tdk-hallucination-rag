"""Integrity-checked EXP-044 challenge loader for the Arena's recorded mode."""
import copy
import hashlib
import json
from pathlib import Path

from src.verification.independent_answer import verify_saved_extraction
from src.verification.release_policy import ABSTENTION

ROOT = Path(__file__).resolve().parents[2]
RAW = 'results/raw/exp044_fresh_transfer.jsonl'
MANIFEST = 'results/raw/exp044_fresh_transfer_manifest.json'
SUMMARY = 'results/processed/exp044_fresh_transfer_summary.json'
FIXTURE = 'data/synthetic/exp044_generated_transfer_cases.json'
PINNED = {
    RAW: '1cee1a96ddedbebf31fc2c770efba608d8c28df4f37ee703121ce18852ce999c',
    MANIFEST: '1034c741ee54a83bac6196f490908f986112a38d814c5b395fae181a3f639d7d',
    SUMMARY: '9e94ebd1ffd447aab0be8e0728defc70654f185fe81940eb19ff4e6963c875b6',
}
FAMILIES = {
    'clean': 'Clean evidence', 'paraphrase': 'Same fact, different wording',
    'negated_distractor': 'Negated distractor', 'conflict': 'Conflicting sources',
    'no_target_evidence': 'Wrong-year evidence', 'false_source_only': 'False source',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_challenge(case, row):
    if (case['case_id'] != row['case_id'] or case['question'] != row['question']
            or list(case['documents'].items()) != list(row['documents'].items())):
        raise ValueError('Question or ordered sources differ from the authored fixture')
    replay = verify_saved_extraction(row['question'], row['documents'], row['answers']['S1'],
                                     row['calls']['V3']['output'])
    if replay != row['candidate_verification']:
        raise ValueError('Saved candidate trace differs from shared-code replay')
    verdict = replay['decision']['verdict']
    expected = row['answers']['S1'] if verdict == 'VERIFIED' else ABSTENTION
    if row['answers']['Candidate_NS'] != expected:
        raise ValueError('Saved candidate answer differs from release policy')
    arm_specs = (
        ('S1', 'Standard RAG draft', ('S1',), None, 'DRAFT', {}, 0),
        ('Original_NS', 'Original NS', ('S1', 'V2'),
         row['original_policy']['decision']['verdict'], row['original_policy']['action'],
         row['original_policy'], row['original_verification']['validation_and_rules_latency_seconds']
         + row['original_policy']['policy_latency_seconds']),
        ('Candidate_NS', 'Candidate NS', ('S1', 'V3'), verdict,
         row['candidate_action'], replay, row['candidate_rule_latency_seconds']),
    )
    systems = []
    for arm, name, stages, result, action, trace, rules_seconds in arm_specs:
        systems.append({
            'system_id': arm, 'name': name, 'answer': row['answers'][arm],
            'verdict': result, 'action': action, 'score': copy.deepcopy(row['scores'][arm]),
            'trace': copy.deepcopy(trace), 'recorded': True,
            'latency_seconds': sum(row['calls'][s]['latency_seconds'] for s in stages) + rules_seconds,
            'input_tokens': sum(row['calls'][s]['input_tokens'] for s in stages),
            'output_tokens': sum(row['calls'][s]['output_tokens'] for s in stages),
            'calls': len(stages),
        })
    return {'case_id': case['case_id'], 'question': case['question'],
            'documents': copy.deepcopy(case['documents']), 'family': case['family'],
            'family_label': FAMILIES[case['family']],
            'authored_reference': case['authored_truth'], 'systems': systems,
            'raw_record': copy.deepcopy(row)}


def load_challenges(root=ROOT):
    root = Path(root)
    for relative, expected in PINNED.items():
        if sha(root / relative) != expected:
            raise ValueError(f'Historical artifact failed integrity check: {relative}')
    manifest = json.loads((root / MANIFEST).read_text())
    if sha(root / FIXTURE) != manifest['source_sha256'][FIXTURE]:
        raise ValueError('Challenge fixture failed integrity check')
    cases = json.loads((root / FIXTURE).read_text())['cases']
    rows = [json.loads(line) for line in (root / RAW).read_text().splitlines()]
    if len(cases) != 24 or len(rows) != 24 or len({c['case_id'] for c in cases}) != 24:
        raise ValueError('Expected all 24 unique recorded cases')
    return [build_challenge(case, row) for case, row in zip(cases, rows)]


def export_challenge(challenge):
    return json.dumps({
        'artifact_type': 'arena_recorded_case_export', 'experiment_id': 'EXP-044',
        'mode': 'recorded_replay', 'new_model_calls': 0,
        'source_sha256': PINNED,
        'question': challenge['question'], 'case_id': challenge['case_id'],
        'family': challenge['family'], 'authored_reference': challenge['authored_reference'],
        'documents': challenge['documents'],
        'recorded_systems': challenge['systems'], 'original_raw_record': challenge['raw_record'],
        'scope': 'Fictional source-consistency demonstration; not external factual verification.',
    }, indent=2, ensure_ascii=False)
