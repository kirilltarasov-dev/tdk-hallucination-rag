from dataclasses import dataclass


ROUTING_DECISIONS = {
    "VERIFY",
    "SKIP",
}


@dataclass
class VerificationRoutingResult:
    decision: str
    reason: str
    raw_output: str


class VerificationRouter:
    def __init__(self, model):
        self.model = model

    def route(
        self,
        question: str,
        documents: list[str],
        answer: str,
    ) -> VerificationRoutingResult:

        documents_text = "\n\n".join(
            f"[Document {i + 1}]\n{document}"
            for i, document in enumerate(documents)
        )

        system_prompt = """
You are a verification-routing component.

Your task is to decide whether a generated answer requires
additional verification against the provided documents.

Choose exactly ONE decision:

SKIP
Use SKIP when the important claims in the generated answer are
clearly and sufficiently supported by the provided documents and
there is no meaningful evidence of contradiction, unsupported
inference, or missing support.

VERIFY
Use VERIFY when additional verification is warranted because at
least one important part of the generated answer may be:
- unsupported by the provided documents;
- inconsistent with the provided documents;
- based on ambiguous or conflicting evidence;
- dependent on combining multiple pieces of evidence where support
  is uncertain;
- a stronger inference than the documents justify.

Important rules:

- Evaluate the generated answer against the provided documents.
- Do not use outside knowledge.
- Do not answer the original question.
- Do not correct the generated answer.
- Do not assume that an answer is correct simply because it sounds
  plausible.
- Do not choose VERIFY merely because verification is possible.
  Choose VERIFY only when there is a meaningful reason for
  additional checking.
- Choose exactly one decision.

Return exactly:

DECISION: <VERIFY|SKIP>
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
    def _parse(raw_output: str) -> VerificationRoutingResult:
        decision = "PARSE_ERROR"
        reason = ""

        for line in raw_output.splitlines():
            line = line.strip()

            if line.upper().startswith("DECISION:"):
                value = line.split(":", 1)[1].strip().upper()

                if value in ROUTING_DECISIONS:
                    decision = value

            elif line.upper().startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()

        return VerificationRoutingResult(
            decision=decision,
            reason=reason,
            raw_output=raw_output,
        )