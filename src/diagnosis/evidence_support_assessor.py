from dataclasses import dataclass

from src.models.mistral import MistralModel


VALID_LABELS = {
    "DIRECT",
    "INFERENTIAL",
    "TOPICAL",
    "NO_SUPPORT",
}

SUPPORT_LABELS = {
    "DIRECT",
    "INFERENTIAL",
}


@dataclass
class EvidenceSupportResult:
    label: str
    supports_answer: bool
    reason: str
    raw_output: str


class EvidenceSupportAssessor:
    """
    Assess whether one document provides answer-supporting evidence
    for a specific question.

    This is stricter than general topical relevance.
    """

    def __init__(self, model: MistralModel):
        self.model = model

    def assess(
        self,
        question: str,
        document: str,
        max_tokens: int = 64,
    ) -> EvidenceSupportResult:

        prompt = self._build_prompt(
            question=question,
            document=document,
        )

        raw_output = self.model.generate(
            user_prompt=prompt,
            max_tokens=max_tokens,
        )

        label, reason = self._parse_output(
            raw_output
        )

        return EvidenceSupportResult(
            label=label,
            supports_answer=label in SUPPORT_LABELS,
            reason=reason,
            raw_output=raw_output,
        )

    @staticmethod
    def _build_prompt(
        question: str,
        document: str,
    ) -> str:

        return f"""
Evaluate how the document supports answering the question.

Do NOT answer the question itself.
Do NOT use outside knowledge.
Evaluate only the evidence contained in this document.

Classify the document as exactly one of:

DIRECT
The document explicitly states the information needed to answer
the question.

INFERENTIAL
The document contains enough evidence to answer the question,
but a simple inference is required, such as interpreting a score,
paraphrase, coreference, or combining statements within this
document.

TOPICAL
The document discusses the same entity or topic, but it does not
provide evidence for the specific fact requested by the question.
This includes documents about the wrong year, event, platform,
relationship, status, or other important constraint.

NO_SUPPORT
The document does not provide useful evidence for answering
the question.

Important:

- Topic or entity overlap alone is NOT answer support.
- Respect dates, years, platforms, events, roles, and other
  constraints in the question.
- Do not guess a requested fact from information about another
  year or a related event.
- A document does not need to contain the final answer verbatim
  if the answer follows through a simple inference.
- Use INFERENTIAL only when the requested answer can reasonably
  be derived from the document itself.

Return exactly:

LABEL: <DIRECT | INFERENTIAL | TOPICAL | NO_SUPPORT>
REASON: <one short sentence>

Question:
{question}

Document:
{document}
""".strip()

    @staticmethod
    def _parse_output(
        raw_output: str,
    ) -> tuple[str, str]:

        label = "PARSE_ERROR"
        reason = ""

        for line in raw_output.splitlines():
            line = line.strip()

            if line.startswith("LABEL:"):
                candidate = (
                    line.split(":", 1)[1]
                    .strip()
                    .upper()
                )

                if candidate in VALID_LABELS:
                    label = candidate

            elif line.startswith("REASON:"):
                reason = (
                    line.split(":", 1)[1]
                    .strip()
                )

        return label, reason