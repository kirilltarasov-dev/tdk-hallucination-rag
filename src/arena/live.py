"""Shared S1 / S2-style / NS interface, with injected generation and no oracle."""
import hashlib
import json
import time

from experiments.exp040_generated_answers import MODEL, REVISION, prompt
from src.verification.independent_answer import verify_saved_extraction
from src.verification.prompt_polarity import build_prompt_v3
from src.verification.release_policy import ABSTENTION

SYSTEMS = ('S1', 'S2', 'Candidate_NS')


def validate_input(question, passages):
    if not isinstance(question, str) or not question.strip() or len(question) > 500:
        raise ValueError('Question must contain 1–500 characters')
    if not isinstance(passages, dict) or not 1 <= len(passages) <= 20:
        raise ValueError('Provide 1–20 ordered source passages')
    for key, text in passages.items():
        if not isinstance(key, str) or not key.strip() or len(key) > 40:
            raise ValueError('Invalid source ID')
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise ValueError('Each source must contain 1–2,000 characters')
    if sum(len(text) for text in passages.values()) > 12000:
        raise ValueError('Combined sources exceed 12,000 characters')


def input_hash(question, passages):
    validate_input(question, passages)
    payload = json.dumps([question, list(passages.items())], ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def answer(question, passages, *, system, generate, draft_call=None):
    """One common interface; generation is injected so tests never load a model."""
    validate_input(question, passages)
    if system not in SYSTEMS:
        raise ValueError('Unknown Arena system')
    case = {'question': question, 'documents': passages}
    draft_call = draft_call or generate('S1', prompt(case), 128)
    if draft_call['stage'] != 'S1' or draft_call['prompt'] != prompt(case):
        raise ValueError('Shared draft belongs to different inputs')
    draft = draft_call['output']
    calls = {'S1': draft_call}
    result, verdict, action, trace, rules_seconds = draft, None, 'DRAFT', {}, 0.0
    if system == 'S2':
        calls['S2'] = generate('S2', prompt(case, draft), 128)
        result, action = calls['S2']['output'], 'SELF_REVIEWED'
        trace = {'method': 'same_model_review_exp040_prompt', 'shared_draft': draft,
                 'symbolic_verification': False, 'factual_truth_verified': False}
    elif system == 'Candidate_NS':
        calls['V3'] = generate('V3', build_prompt_v3(question, passages, draft), 1024)
        started = time.perf_counter()
        trace = verify_saved_extraction(question, passages, draft, calls['V3']['output'])
        rules_seconds = time.perf_counter() - started
        verdict = trace['decision']['verdict']
        action = 'RELEASE' if verdict == 'VERIFIED' else 'ABSTAIN'
        result = draft if action == 'RELEASE' else ABSTENTION
    return {
        'system_id': system,
        'name': {'S1': 'Standard RAG draft', 'S2': 'Self-review (S2)',
                 'Candidate_NS': 'Neuro-symbolic'}[system],
        'answer': result, 'verdict': verdict, 'action': action, 'trace': trace,
        'recorded': False, 'stage_calls': calls, 'calls': len(calls),
        'rules_latency_seconds': rules_seconds,
        'latency_seconds': sum(c['latency_seconds'] for c in calls.values()) + rules_seconds,
        'input_tokens': sum(c['input_tokens'] for c in calls.values()),
        'output_tokens': sum(c['output_tokens'] for c in calls.values()),
    }


def run_round(question, passages, generate):
    s1 = answer(question, passages, system='S1', generate=generate)
    draft = s1['stage_calls']['S1']
    s2 = answer(question, passages, system='S2', generate=generate, draft_call=draft)
    ns = answer(question, passages, system='Candidate_NS', generate=generate, draft_call=draft)
    return {'artifact_type': 'arena_live_demonstration_round', 'mode': 'live_local',
            'input_hash': input_hash(question, passages), 'question': question,
            'documents': passages, 'model': MODEL, 'model_revision': REVISION,
            'temperature': 0, 'systems': [s1, s2, ns],
            'calls': {'S1': draft, 'S2': s2['stage_calls']['S2'], 'V3': ns['stage_calls']['V3']},
            'research_scope': 'Demonstration only; not an independent evaluation experiment.'}


def stable(value):
    if isinstance(value, dict):
        return {key: stable(item) for key, item in value.items() if not key.endswith('_seconds')}
    if isinstance(value, list):
        return [stable(item) for item in value]
    return value


def verify_round(result, question, passages):
    if result.get('input_hash') != input_hash(question, passages):
        raise ValueError('Live result belongs to different ordered inputs')
    if set(result.get('calls', {})) != {'S1', 'S2', 'V3'}:
        raise ValueError('Expected exactly three completed calls')
    def replay(stage, user_prompt, max_tokens):
        call = result['calls'][stage]
        if (call['stage'], call['prompt'], call['max_tokens']) != (stage, user_prompt, max_tokens):
            raise ValueError('Saved live call differs from current prompt contract')
        return call
    expected = run_round(question, passages, replay)
    if stable(expected) != stable(result):
        raise ValueError('Live result fails deterministic replay')
    return result
