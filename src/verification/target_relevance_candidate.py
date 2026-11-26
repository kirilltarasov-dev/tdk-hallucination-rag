"""Development-only target-complete source check for the finite winner grammar.

This candidate is distinct from the frozen EXP-046 method. It preserves strict
neural extraction validation, but does not demand neural copies of affirmative
statements about unrelated events or years. Full source text is still parsed
to detect unsupported syntax, target omissions and conflicts. Neither variant
establishes source credibility or natural-language entailment.
"""

from src.verification.independent_answer import canonical, read_answer
from src.verification.neuro_symbolic import ExtractionError, parse_extraction
from src.verification.polarity_guard import statement
from src.verification.release_policy import ABSTENTION
from src.verification.symbolic_rules import AnswerClaim, EvidenceFact, QuestionFrame, verify_structured_answer


VERSION = 'target_complete_neural_development_v1'
RULE_ONLY_VERSION = 'finite_source_rule_only_development_v1'


def _unknown(rule):
    return {'verdict': 'UNKNOWN', 'rule_id': rule}


def _same_fact(fact, parsed):
    return (fact.relation == 'won' and fact.subject is None
            and fact.year == parsed['year']
            and canonical(fact.event) == canonical(parsed['event'])
            and canonical(fact.value) == canonical(parsed['value']))


def _inputs(question, documents, response):
    answer = read_answer(question, response)
    if answer['status'] == 'UNRESOLVED':
        return None, None, _unknown('ANSWER_UNRESOLVED')
    frame = QuestionFrame(**answer['question_frame'])
    parsed = {}
    for source_id, text in documents.items():
        item = statement(text)
        if item is None:
            return None, None, _unknown('UNSUPPORTED_SOURCE_GRAMMAR')
        parsed[source_id] = item
    return frame, (answer, parsed), None


def _decision(frame, answer, parsed, documents, facts):
    positives = {canonical(item['value']) for item in parsed.values()
                 if item['polarity'] == 1 and item['year'] == frame.year
                 and canonical(item['event']) == canonical(frame.event)}
    negatives = {canonical(item['value']) for item in parsed.values()
                 if item['polarity'] == -1 and item['year'] == frame.year
                 and canonical(item['event']) == canonical(frame.event)}
    if positives & negatives:
        return {'verdict': 'CONFLICT', 'rule_id': 'TARGET_POSITIVE_NEGATIVE_CONFLICT'}
    claim = AnswerClaim(answer['value'], answer['status'] == 'ABSTENTION')
    return verify_structured_answer(frame, facts, claim).trace()


def rule_only_decision(question, documents, response):
    """Comparator that parses each full controlled-language source directly."""
    frame, data, error = _inputs(question, documents, response)
    if error:
        return error
    answer, parsed = data
    facts = [EvidenceFact(source_id=source_id, source_span=documents[source_id],
                          relation='won', event=item['event'],
                          year=item['year'], value=item['value'])
             for source_id, item in parsed.items() if item['polarity'] == 1]
    return _decision(frame, answer, parsed, documents, facts)


def target_complete_decision(question, documents, response, raw_extraction):
    """Check every neural fact but require coverage only for target sources."""
    frame, data, error = _inputs(question, documents, response)
    if error:
        return error
    answer, parsed = data
    try:
        extraction = parse_extraction(raw_extraction, question, documents, response)
    except ExtractionError:
        return _unknown('NEURAL_EXTRACTION_INVALID')
    if extraction.question is None or any(
            canonical(getattr(frame, key)) != canonical(getattr(extraction.question, key))
            for key in ('relation', 'event', 'year', 'subject')):
        return _unknown('QUESTION_FRAME_MISMATCH')
    for source_id, item in parsed.items():
        is_target = item['year'] == frame.year and canonical(item['event']) == canonical(frame.event)
        source_facts = [fact for fact in extraction.facts if fact.source_id == source_id]
        if f'document:{source_id}' in extraction.unresolved and is_target:
            return _unknown('TARGET_SOURCE_UNRESOLVED')
        if item['polarity'] == -1:
            if source_facts:
                return _unknown('NEGATIVE_EXTRACTED_AS_POSITIVE')
        else:
            if any(not _same_fact(fact, item) for fact in source_facts):
                return _unknown('NEURAL_SOURCE_MISMATCH')
            if is_target and len(source_facts) != 1:
                return _unknown('TARGET_SOURCE_COVERAGE')
            if len(source_facts) > 1:
                return _unknown('DUPLICATE_NEURAL_FACT')
    facts = [fact for fact in extraction.facts if fact.year == frame.year
             and canonical(fact.event) == canonical(frame.event)]
    return _decision(frame, answer, parsed, documents, facts)


def release(response, decision):
    """Return the unchanged draft only for an evidence-relative VERIFIED."""
    return response if decision['verdict'] == 'VERIFIED' else ABSTENTION
