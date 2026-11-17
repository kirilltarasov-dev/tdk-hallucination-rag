"""Release a draft only after the existing combined verifier accepts it.

This policy checks source consistency in a restricted language. It does not
establish factual truth, select trustworthy sources, or repair the answer.
"""
import time

from src.verification.neuro_symbolic import parse_extraction
from src.verification.prompt_clarity import verify_text_v2
from src.verification.relation_guard import apply_relation_guard
from src.verification.answer_claim_guard import apply_answer_claim_guard

POLICY_VERSION = 'verified_release_else_abstain_v1'
ABSTENTION = 'I cannot determine the winner.'


def release_from_verification(question, documents, draft, verification):
    """Replay the unchanged guards and make an explicit release decision."""
    start = time.perf_counter()
    predicate = answer = None
    decision = verification['decision']
    if verification['validation_error'] is None:
        extraction = parse_extraction(verification['raw_extraction'], question, documents, draft)
        predicate = apply_relation_guard(question, documents, extraction)
        answer = apply_answer_claim_guard(draft, extraction, predicate['decision'])
        decision = answer['decision']
    if decision['verdict'] not in {'VERIFIED', 'REFUTED', 'CONFLICT', 'UNKNOWN'}:
        raise ValueError('Unknown verification verdict')
    released = decision['verdict'] == 'VERIFIED'
    return {'policy_version': POLICY_VERSION,
            'action': 'RELEASE' if released else 'ABSTAIN',
            'final_answer': draft if released else ABSTENTION,
            'factual_truth_verified': False, 'decision': decision,
            'predicate_trace': predicate, 'answer_trace': answer,
            'policy_latency_seconds': time.perf_counter() - start}


def verify_and_release(question, documents, draft, generate):
    verification = verify_text_v2(question, documents, draft, generate)
    return {'verification': verification,
            'policy': release_from_verification(question, documents, draft, verification)}
