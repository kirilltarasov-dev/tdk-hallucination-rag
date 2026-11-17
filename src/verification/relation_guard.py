"""Conservative controlled-language guard for the narrow 'won' predicate.

This is a scope restriction, not a general natural-language entailment parser.
It checks full source documents to avoid approving a positive quotation taken
out of a negating or reporting context. It does not check claim completeness.
"""

import re

from src.verification.neuro_symbolic import Extraction, apply_extraction
from src.verification.symbolic_rules import RuleResult


GUARD_VERSION = "event_winner_relation_guard_v1"
RESERVED_WORDS = {
    "and", "or", "not", "never", "neither", "nor", "if", "unless",
    "said", "says", "reported", "reportedly", "claimed", "claims",
    "denied", "false", "true", "possibly", "probably", "allegedly",
}


def _canonical(text):
    return " ".join(text.casefold().split())


def _name_supported(value):
    # Deliberately excludes punctuation-rich names and logical/reporting clauses.
    return (
        isinstance(value, str) and len(value) <= 100
        and re.fullmatch(r"[A-Za-z0-9]+(?:[ '\-][A-Za-z0-9]+)*", value) is not None
        and not (set(re.findall(r"[a-z0-9]+", value.casefold())) & RESERVED_WORDS)
    )


def _matches_template(text, templates, terminal):
    candidate = _canonical(text)
    accepted = {_canonical(template) for template in templates}
    return candidate in accepted or (
        candidate.endswith(terminal) and candidate[:-1] in accepted
    )


def question_relation_supported(question, frame):
    if (frame.relation != "won" or frame.subject is not None
            or type(frame.year) is not int or not 1000 <= frame.year <= 9999
            or not _name_supported(frame.event)):
        return False
    event, year = frame.event, frame.year
    templates = []
    for determiner in ("", "the "):
        for subject in ("Who", "Which team", "Which player", "Which competitor"):
            templates.extend((
                f"{subject} won {determiner}{year} {event}",
                f"{subject} won {determiner}{event} in {year}",
            ))
        templates.append(f"Who was the winner of {determiner}{year} {event}")
    return _matches_template(question, templates, "?")


def fact_relation_supported(document, fact):
    if (fact.relation != "won" or fact.subject is not None
            or type(fact.year) is not int or not 1000 <= fact.year <= 9999
            or not _name_supported(fact.event) or not _name_supported(fact.value)):
        return False
    value, event, year = fact.value, fact.event, fact.year
    templates = []
    for determiner in ("", "the "):
        templates.extend((
            f"{value} won {determiner}{year} {event}",
            f"{value} won {determiner}{event} in {year}",
            f"{determiner}{year} {event} was won by {value}",
            f"The winner of {determiner}{year} {event} was {value}",
        ))
    return _matches_template(document, templates, ".")


def apply_relation_guard(question: str, documents: dict[str, str],
                         extraction: Extraction) -> dict:
    """Only preserve the old decision or replace it with a traced UNKNOWN."""
    baseline = apply_extraction(extraction)
    if extraction.question is None or extraction.unresolved:
        return {
            "guard_version": GUARD_VERSION, "status": "NOT_EVALUATED_UNRESOLVED",
            "checks": [], "decision": baseline.trace(),
        }
    checks = [{
        "kind": "question_relation", "passed": question_relation_supported(question, extraction.question),
        "text": question, "event": extraction.question.event, "year": extraction.question.year,
    }]
    # Check every extracted fact, including facts that later fail event/year
    # matching. Blocking on an unsupported irrelevant fact is a coverage cost.
    for index, fact in enumerate(extraction.facts):
        document = documents.get(fact.source_id)
        passed = (
            isinstance(document, str)
            and fact.source_span in document
            and fact_relation_supported(document, fact)
        )
        checks.append({
            "kind": "document_relation", "fact_index": index,
            "source_id": fact.source_id, "passed": passed,
            "full_source_text": document, "quoted_span": fact.source_span,
            "event": fact.event, "year": fact.year, "value": fact.value,
        })
    failed = [check for check in checks if not check["passed"]]
    if failed:
        rule = ("G1_QUESTION_RELATION" if not checks[0]["passed"]
                else "G2_FACT_RELATION")
        decision = RuleResult(
            "UNKNOWN", rule,
            "The question or a full fact source is outside the declared affirmative-win grammar.",
            (),
        )
        return {"guard_version": GUARD_VERSION, "status": "BLOCKED",
                "checks": checks, "decision": decision.trace()}
    return {"guard_version": GUARD_VERSION, "status": "PASSED",
            "checks": checks, "decision": baseline.trace()}
