from dataclasses import dataclass


CLAIM_TYPES = {
    "FACTUAL",
    "LOGICAL",
    "NUMERICAL",
    "MIXED",
    "NONE",
}


@dataclass
class ClaimRoutingResult:
    claim_type: str
    reason: str
    raw_output: str


class ClaimRouter:
    def __init__(self, model):
        self.model = model

    def classify(
        self,
        question: str,
        documents: list[str],
        answer: str,
    ) -> ClaimRoutingResult:

        documents_text = "\n\n".join(
            f"[Document {i + 1}]\n{document}"
            for i, document in enumerate(documents)
        )

        system_prompt = """
You are a claim-type classifier.

Your task is to determine what kind of verification is required
for the generated answer.

Classify the answer into exactly ONE of these categories:

FACTUAL
The answer mainly contains factual claims that should be checked
against the provided documents.

LOGICAL
The answer mainly depends on logical reasoning, consistency,
constraints, or deduction rather than directly stated facts.

NUMERICAL
The answer mainly depends on arithmetic, numerical computation,
comparison, or another calculation that should be checked
computationally.

MIXED
The answer contains multiple important claim types and cannot
reasonably be verified using only one of the categories above.

NONE
The answer contains no meaningful claim requiring verification,
for example an abstention or a statement that the available
information is insufficient.

Important rules:

- Classify the GENERATED ANSWER, not the question alone.
- Use the question and documents only to understand what the
  generated answer is claiming.
- Do not judge whether the answer is correct.
- Do not correct the answer.
- Do not answer the original question.
- Do not use outside knowledge.
- Choose exactly one category.

Return exactly:

TYPE: <FACTUAL|LOGICAL|NUMERICAL|MIXED|NONE>
REASON: <brief explanation>
""".strip()

        user_prompt = f"""
Question:
{question}

Documents:
{documents_text}

Generated answer:
{answer}
""".strip()

        raw_output = self.model.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=96,
        ).strip()

        return self._parse(raw_output)

    @staticmethod
    def _parse(raw_output: str) -> ClaimRoutingResult:
        claim_type = "PARSE_ERROR"
        reason = ""

        for line in raw_output.splitlines():
            line = line.strip()

            if line.upper().startswith("TYPE:"):
                value = line.split(":", 1)[1].strip().upper()

                if value in CLAIM_TYPES:
                    claim_type = value

            elif line.upper().startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()

        return ClaimRoutingResult(
            claim_type=claim_type,
            reason=reason,
            raw_output=raw_output,
        )