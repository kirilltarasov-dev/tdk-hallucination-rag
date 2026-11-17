"""Versioned full-document checks for a finite positive/negative win grammar.

This is a narrow symbolic audit, not general NLI or source credibility checking.
It never fills missing neural facts or silently repairs a malformed extraction.
"""
import re

from src.verification.neuro_symbolic import apply_extraction
from src.verification.relation_guard import _name_supported, question_relation_supported
from src.verification.symbolic_rules import RuleResult

GUARD_VERSION = 'event_winner_polarity_and_coverage_v2'
NAME = r"[A-Za-z0-9]+(?:[ '\-][A-Za-z0-9]+)*?"


def canonical(value):
    return ' '.join(value.casefold().split())


def statement(document):
    """Read exactly one whole controlled-language sentence, or return None."""
    value, event, year = rf'(?P<value>{NAME})', rf'(?P<event>{NAME})', r'(?P<year>[1-9][0-9]{3})'
    patterns = []
    for polarity, verb in [(1,'won'), (-1,'did not win'),
                           (1,'took first place in'), (-1,'did not take first place in')]:
        patterns.extend([(polarity, rf'{value}\s+{verb}\s+(?:the\s+)?{year}\s+{event}'),
                         (polarity, rf'{value}\s+{verb}\s+(?:the\s+)?{event}\s+in\s+{year}')])
    patterns.extend([(1,rf'(?:the\s+)?{year}\s+{event}\s+was won by\s+{value}'),
                     (1,rf'The winner of (?:the\s+)?{year}\s+{event}\s+was\s+{value}')])
    text = document.strip()
    for polarity, pattern in patterns:
        match = re.fullmatch(pattern + r'\.?', text, re.IGNORECASE)
        if match and _name_supported(match['value']) and _name_supported(match['event']):
            return {**match.groupdict(), 'year':int(match['year']), 'polarity':polarity}
    return None


def apply_polarity_guard(question, documents, extraction):
    baseline = apply_extraction(extraction)
    checks = []

    def result(status, decision):
        return {'guard_version':GUARD_VERSION, 'status':status,
                'source_checks':checks, 'decision':decision}

    def blocked(rule, reason):
        return result('BLOCKED', RuleResult('UNKNOWN',rule,reason,()).trace())

    if extraction.question is None or extraction.unresolved:
        return result('NOT_EVALUATED_UNRESOLVED',baseline.trace())
    frame = extraction.question
    if not question_relation_supported(question,frame):
        return blocked('G1_QUESTION_RELATION','Question is outside the frozen question grammar.')
    if any(f.source_id not in documents for f in extraction.facts):
        return blocked('G4_SOURCE_COVERAGE','Extracted fact refers to an absent document.')
    for source_id, document in documents.items():
        parsed = statement(document)
        facts = [f for f in extraction.facts if f.source_id==source_id]
        check = {'source_id':source_id,'full_source_text':document,'statement':parsed,
                 'neural_fact_count':len(facts),'matched':False}
        checks.append(check)
        if parsed is None:
            return blocked('G4_UNSUPPORTED_SOURCE','A full source is outside the declared statement grammar.')
        if parsed['polarity'] == -1:
            if facts:
                return blocked('G4_NEGATIVE_AS_POSITIVE','A negative win was extracted as a positive fact.')
        else:
            if len(facts) != 1:
                return blocked('G4_SOURCE_COVERAGE','An affirmative source must have exactly one extracted win fact.')
            fact = facts[0]
            if (fact.relation!='won' or fact.subject is not None or fact.source_span not in document
                or fact.year!=parsed['year'] or canonical(fact.event)!=canonical(parsed['event'])
                or canonical(fact.value)!=canonical(parsed['value'])):
                return blocked('G4_SOURCE_MISMATCH','Neural fact differs from the full controlled-language statement.')
        check['matched'] = True
    matching = [c for c in checks if c['statement']['year']==frame.year
                and canonical(c['statement']['event'])==canonical(frame.event)]
    positive = {canonical(c['statement']['value']) for c in matching if c['statement']['polarity']==1}
    negative = {canonical(c['statement']['value']) for c in matching if c['statement']['polarity']==-1}
    if positive & negative:
        return result('CONFLICT',RuleResult('CONFLICT','G4_POSITIVE_NEGATIVE_CONFLICT',
                      'The same target win is affirmed and denied by the supplied sources.',()).trace())
    return result('PASSED',baseline.trace())
