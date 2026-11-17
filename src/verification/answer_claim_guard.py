"""Finite-language audit of all target-answer assertions in a full response.

No semantic inference or truth checking is performed outside the listed
templates. Unconsumed text blocks a decisive verdict rather than being ignored.
"""

import re

from src.verification.relation_guard import _name_supported
from src.verification.symbolic_rules import RuleResult


GUARD_VERSION = "answer_claim_inventory_v1"
NAME = r"[A-Za-z0-9]+(?:[ '\-][A-Za-z0-9]+)*?"
END = r"(?:\.(?=\s|$)|(?=$))"
ABSTENTIONS = (
    "I cannot determine the winner",
    "I do not know who won",
    "There is insufficient information to answer",
    "Insufficient information",
)


def _canonical(value):
    return " ".join(value.casefold().split())


def inventory_answer(response, frame):
    """Consume the complete response and retain asserted and rejected values."""
    event, year = re.escape(frame.event), str(frame.year)
    target = rf"(?:\s+(?:the\s+)?{year}\s+{event}|\s+(?:the\s+)?{event}\s+in\s+{year})?"
    patterns = [
        ("rejected_quote", rf'The\s+claim\s+"(?P<rejected>{NAME})\s+won\.?"\s+is\s+false'),
        ("contrast", rf"(?P<asserted>{NAME})\s+won,\s+not\s+(?P<rejected>{NAME})"),
        ("rejection", rf"(?P<rejected>{NAME})\s+did\s+not\s+win{target}"),
        ("assertion", rf"(?P<asserted>{NAME})\s+won{target}"),
    ]
    compiled = [(kind, re.compile(pattern + END, re.IGNORECASE)) for kind, pattern in patterns]
    compiled += [("abstention", re.compile(re.escape(text) + END, re.IGNORECASE))
                 for text in ABSTENTIONS]
    units, asserted, rejected = [], [], []
    abstained = False
    offset = 0
    while offset < len(response):
        if response[offset].isspace():
            offset += 1
            continue
        matched = False
        for kind, pattern in compiled:
            match = pattern.match(response, offset)
            if match is None:
                continue
            values = {key: value for key, value in match.groupdict().items() if value is not None}
            if not all(_name_supported(value) for value in values.values()):
                continue
            units.append({"kind": kind, "start": offset, "end": match.end(),
                          "text": response[offset:match.end()], **values})
            if "asserted" in values:
                asserted.append(values["asserted"])
            if "rejected" in values:
                rejected.append(values["rejected"])
            abstained |= kind == "abstention"
            offset = match.end()
            matched = True
            break
        if not matched:
            return {"status": "UNSUPPORTED", "units": units, "asserted_values": asserted,
                    "rejected_values": rejected, "abstention_detected": abstained,
                    "unsupported_offset": offset, "unconsumed_text": response[offset:]}
    return {"status": "COMPLETE", "units": units, "asserted_values": asserted,
            "rejected_values": rejected, "abstention_detected": abstained,
            "unsupported_offset": None, "unconsumed_text": ""}


def apply_answer_claim_guard(response, extraction, prior_decision):
    """Preserve a prior verdict only when the full response fits its claim state."""
    if prior_decision["verdict"] == "UNKNOWN":
        return {"guard_version": GUARD_VERSION, "status": "NOT_EVALUATED_PRIOR_UNKNOWN",
                "inventory": None, "decision": prior_decision}
    if extraction.question is None or extraction.unresolved:
        raise ValueError("A decisive prior verdict requires a resolved extraction")
    inventory = inventory_answer(response, extraction.question)
    positive = {_canonical(value) for value in inventory["asserted_values"]}
    negative = {_canonical(value) for value in inventory["rejected_values"]}
    rule, explanation = None, None
    if inventory["status"] != "COMPLETE":
        rule, explanation = "G3_UNSUPPORTED_ANSWER", "Part of the response is outside the declared claim grammar."
    elif len(positive) > 1:
        rule, explanation = "G3_INCOMPATIBLE_ANSWERS", "The full response asserts more than one distinct target winner."
    elif positive & negative:
        rule, explanation = "G3_ASSERTION_NEGATION_CONFLICT", "The response both asserts and rejects the same winner."
    elif positive and inventory["abstention_detected"]:
        rule, explanation = "G3_MIXED_ABSTENTION", "The response both abstains and asserts a winner."
    elif extraction.answer.abstained:
        if positive or not inventory["abstention_detected"]:
            rule, explanation = "G3_ANSWER_STATE_MISMATCH", "The full response does not support the extracted abstention state."
    elif (inventory["abstention_detected"] or len(positive) != 1
          or extraction.answer.value is None
          or _canonical(extraction.answer.value) not in positive):
        rule, explanation = "G3_ANSWER_STATE_MISMATCH", "The full response differs from the single extracted answer claim."
    if rule is not None:
        decision = RuleResult("UNKNOWN", rule, explanation, ()).trace()
        return {"guard_version": GUARD_VERSION, "status": "BLOCKED",
                "inventory": inventory, "decision": decision}
    return {"guard_version": GUARD_VERSION, "status": "PASSED",
            "inventory": inventory, "decision": prior_decision}
