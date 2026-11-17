from dataclasses import dataclass

from src.models.mistral import MistralModel


VALID_LABELS = {
    "RELEVANT",
    "IRRELEVANT",
}


@dataclass
class RelevanceResult:
    label: str
    reason: str
    raw_output: str


class RelevanceDetector:
    """
    Document-level relevance detector.

    The detector receives only:
        - question
        - one document

    It does NOT receive RGB positive/negative labels.
    """

    def __init__(self, model: MistralModel):
        self.model = model

    def classify(
        self,
        question: str,
        document: str,
        max_tokens: int = 64,
    ) -> RelevanceResult:

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

        return RelevanceResult(
            label=label,
            reason=reason,
            raw_output=raw_output,
        )

    @staticmethod
    def _build_prompt(
        question: str,
        document: str,
    ) -> str:

        return f"""
Evaluate whether the document contains information that is useful
for answering the question.

Do NOT answer the question.

Classify the document as exactly one of:

RELEVANT
The document contains information that directly supports answering
the question or provides evidence needed to derive the answer.

IRRELEVANT
The document does not contain information useful for answering
the question.

Important rules:

- Judge only the relationship between the question and the document.
- Do not use outside knowledge to answer the question.
- Do not require the document to contain the complete answer.
- A document is RELEVANT if it provides useful evidence toward the answer.
- Topic similarity alone is not sufficient for relevance.

Return exactly:

LABEL: <RELEVANT | IRRELEVANT>
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