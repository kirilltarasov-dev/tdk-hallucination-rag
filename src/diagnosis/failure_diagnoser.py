from dataclasses import dataclass

from src.models.mistral import MistralModel


VALID_CONDITIONS = {
    "CLEAN",
    "NOISE",
    "CONFLICT",
    "INSUFFICIENT",
}


@dataclass
class DiagnosisResult:
    condition: str
    relevant_documents: int | None
    reason: str
    raw_output: str


class FailureDiagnoser:
    """
    Evidence-condition diagnoser for S3.

    The diagnoser receives only:
        - the user question
        - retrieved documents

    It must NOT receive:
        - gold answers
        - RGB positive/negative labels
        - noise_rate
        - expected condition
    """

    def __init__(self, model: MistralModel):
        self.model = model

    def diagnose(
        self,
        question: str,
        evidence: str,
        max_tokens: int = 128,
    ) -> DiagnosisResult:

        prompt = self._build_prompt(
            question=question,
            evidence=evidence,
        )

        raw_output = self.model.generate(
            user_prompt=prompt,
            max_tokens=max_tokens,
        )

        condition, relevant_documents, reason = (
            self._parse_output(raw_output)
        )

        return DiagnosisResult(
            condition=condition,
            relevant_documents=relevant_documents,
            reason=reason,
            raw_output=raw_output,
        )

    @staticmethod
    def _build_prompt(
        question: str,
        evidence: str,
    ) -> str:

        return f"""
You are evaluating the quality of retrieved documents for answering
a question.

Do NOT answer the question itself.

Classify the retrieved evidence into exactly one of these conditions:

CLEAN
The documents contain sufficient relevant information to answer the
question, and there is no important contradiction or substantial
irrelevant information that would interfere with answering.

NOISE
Sufficient relevant information is present, but it is mixed with
substantial irrelevant or distracting information.

CONFLICT
The documents contain relevant information, but important claims
needed to answer the question contradict each other.

INSUFFICIENT
The documents do not contain enough relevant information to answer
the question reliably.

Important rules:

- Judge only the provided documents.
- Do not use outside knowledge to decide the correct answer.
- Do not answer the question.
- Relevant information means information useful for answering the
  question.
- A document can be relevant even if it does not contain the complete
  answer by itself.
- Use CONFLICT only when relevant claims actually contradict each
  other.
- Use INSUFFICIENT when the provided evidence does not support a
  reliable answer.

Return exactly:

CONDITION: <CLEAN | NOISE | CONFLICT | INSUFFICIENT>
RELEVANT_DOCUMENTS: <integer>
REASON: <one short sentence>

Documents:
{evidence}

Question:
{question}
""".strip()

    @staticmethod
    def _parse_output(
        raw_output: str,
    ) -> tuple[str, int | None, str]:

        condition = "PARSE_ERROR"
        relevant_documents = None
        reason = ""

        for line in raw_output.splitlines():
            line = line.strip()

            if line.startswith("CONDITION:"):
                candidate = (
                    line.split(":", 1)[1]
                    .strip()
                    .upper()
                )

                if candidate in VALID_CONDITIONS:
                    condition = candidate

            elif line.startswith("RELEVANT_DOCUMENTS:"):
                candidate = (
                    line.split(":", 1)[1]
                    .strip()
                )

                try:
                    relevant_documents = int(candidate)
                except ValueError:
                    relevant_documents = None

            elif line.startswith("REASON:"):
                reason = (
                    line.split(":", 1)[1]
                    .strip()
                )

        return (
            condition,
            relevant_documents,
            reason,
        )