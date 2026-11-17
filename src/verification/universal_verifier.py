from dataclasses import dataclass

from src.models.mistral import MistralModel


@dataclass
class VerificationResult:
    verdict: str
    final_answer: str
    raw_output: str


class UniversalVerifier:
    """
    Universal post-generation verifier for S2.

    Every generated draft answer is passed through this verifier,
    regardless of whether the draft appears correct.
    """

    def __init__(self, model: MistralModel):
        self.model = model

    def verify(
        self,
        question: str,
        evidence: str,
        draft_answer: str,
        max_tokens: int = 256,
    ) -> VerificationResult:

        prompt = self._build_prompt(
            question=question,
            evidence=evidence,
            draft_answer=draft_answer,
        )

        raw_output = self.model.generate(
            prompt,
            max_tokens=max_tokens,
        )

        verdict, final_answer = self._parse_output(
            raw_output=raw_output,
            draft_answer=draft_answer,
        )

        return VerificationResult(
            verdict=verdict,
            final_answer=final_answer,
            raw_output=raw_output,
        )

    @staticmethod
    def _build_prompt(
        question: str,
        evidence: str,
        draft_answer: str,
    ) -> str:

        return f"""
You are verifying an answer using only the provided documents.

Determine whether the draft answer is supported by the documents.

Use one of exactly three verdicts:

SUPPORTED
The documents support the draft answer.

UNSUPPORTED
The draft answer is incorrect or contradicted by the documents.
Provide a corrected answer using only the documents.

INSUFFICIENT
The documents do not contain enough reliable information to answer
the question.

Return your result using exactly this format:

VERDICT: SUPPORTED | UNSUPPORTED | INSUFFICIENT
FINAL_ANSWER: <final answer>

If the verdict is SUPPORTED, repeat the original draft answer as
FINAL_ANSWER.

If the verdict is UNSUPPORTED, provide the corrected answer as
FINAL_ANSWER.

If the verdict is INSUFFICIENT, write:
I can not answer the question because of the insufficient information in documents.

Documents:
{evidence}

Question:
{question}

Draft answer:
{draft_answer}
""".strip()

    @staticmethod
    def _parse_output(
        raw_output: str,
        draft_answer: str,
    ) -> tuple[str, str]:

        verdict = "PARSE_ERROR"
        final_answer = draft_answer

        for line in raw_output.splitlines():
            line = line.strip()

            if line.startswith("VERDICT:"):
                candidate = line.split(":", 1)[1].strip().upper()

                if candidate in {
                    "SUPPORTED",
                    "UNSUPPORTED",
                    "INSUFFICIENT",
                }:
                    verdict = candidate

            elif line.startswith("FINAL_ANSWER:"):
                candidate = line.split(":", 1)[1].strip()

                if candidate:
                    final_answer = candidate

        return verdict, final_answer