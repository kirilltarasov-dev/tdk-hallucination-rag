"""Deterministic verification over already structured evidence facts.

This module is an oracle-fact prototype. It does not extract facts from text
and does not itself constitute a measured neuro-symbolic pipeline.
"""

from dataclasses import asdict, dataclass
from typing import Literal


Verdict = Literal["VERIFIED", "REFUTED", "CONFLICT", "UNKNOWN"]


def _canonical(value: str) -> str:
    return " ".join(value.casefold().split())


@dataclass(frozen=True)
class QuestionFrame:
    relation: str
    event: str
    year: int | None = None
    subject: str | None = None


@dataclass(frozen=True)
class EvidenceFact:
    source_id: str
    source_span: str
    relation: str
    event: str
    value: str
    year: int | None = None
    subject: str | None = None


@dataclass(frozen=True)
class AnswerClaim:
    value: str | None = None
    abstained: bool = False


@dataclass(frozen=True)
class RuleResult:
    verdict: Verdict
    rule_id: str
    explanation: str
    matching_facts: tuple[EvidenceFact, ...]

    def trace(self) -> dict:
        return {
            "verdict": self.verdict,
            "rule_id": self.rule_id,
            "explanation": self.explanation,
            "matching_facts": [asdict(fact) for fact in self.matching_facts],
        }


def _matches_question(question: QuestionFrame, fact: EvidenceFact) -> bool:
    if _canonical(question.relation) != _canonical(fact.relation):
        return False
    if _canonical(question.event) != _canonical(fact.event):
        return False
    if question.year is not None and question.year != fact.year:
        return False
    if question.subject is not None and _canonical(question.subject) != _canonical(fact.subject or ""):
        return False
    return True


def verify_structured_answer(
    question: QuestionFrame,
    facts: list[EvidenceFact],
    answer: AnswerClaim,
) -> RuleResult:
    """Apply narrow written rules R3, R5, and R6 to structured inputs.

    R3 requires all specified question constraints to match a fact. R5
    detects disagreement among matching source facts. R6 rejects an answer
    that differs from the unique supported value, or an abstention when such
    a value is present. UNKNOWN is returned when no rule can decide.
    """
    if answer.abstained and answer.value is not None:
        raise ValueError("An abstention cannot also assert an answer value")
    for fact in facts:
        if not fact.source_id or not fact.source_span or not fact.value:
            raise ValueError("Every fact needs a source ID, source span, and value")

    matched = tuple(fact for fact in facts if _matches_question(question, fact))
    if not matched:
        return RuleResult("UNKNOWN", "R3_NO_MATCH",
                          "No structured fact satisfies all question constraints.", ())

    values = {_canonical(fact.value) for fact in matched}
    if len(values) > 1:
        return RuleResult("CONFLICT", "R5_CONFLICT",
                          "Matching sources assert different answer values.", matched)

    supported = matched[0].value
    if answer.abstained:
        return RuleResult("REFUTED", "R6_FALSE_ABSTENTION",
                          f"The answer abstains although matching evidence supports {supported!r}.", matched)
    if answer.value is None:
        return RuleResult("UNKNOWN", "R6_NO_CLAIM",
                          "The response has no structured answer claim.", matched)
    if _canonical(answer.value) != _canonical(supported):
        return RuleResult("REFUTED", "R6_ANSWER_MISMATCH",
                          f"The asserted answer differs from the supported value {supported!r}.", matched)
    return RuleResult("VERIFIED", "R3_R6_SUPPORTED",
                      "The answer equals the value in matching structured evidence.", matched)
