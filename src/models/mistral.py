from mlx_lm import generate, load


class MistralModel:
    def __init__(
        self,
        model_name: str = "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    ):
        print(f"Loading model: {model_name}")

        self.model, self.tokenizer = load(model_name)

        print("Model loaded.")

    def generate(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 256,
    ) -> str:
        if system_prompt:
            content = f"{system_prompt}\n\n{user_prompt}"
        else:
            content = user_prompt

        messages = [
            {
                "role": "user",
                "content": content,
            }
        ]

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        response = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            verbose=False,
        )

        return response.strip()


if __name__ == "__main__":
    model = MistralModel()

    answer = model.generate(
        user_prompt="What is the capital of France?",
        system_prompt=(
            "You are an accurate assistant. "
            "Answer briefly and directly."
        ),
    )

    print(f"Answer: {answer}")