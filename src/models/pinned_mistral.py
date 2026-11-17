"""MLX Mistral wrapper with an explicit Hugging Face revision."""

from mlx_lm import load

from src.models.mistral import MistralModel


class PinnedMistralModel(MistralModel):
    def __init__(self, model_name: str, revision: str):
        if not revision or len(revision) != 40:
            raise ValueError("A full 40-character model revision is required")
        self.model_name = model_name
        self.revision = revision
        print(f"Loading model: {model_name}@{revision}")
        self.model, self.tokenizer = load(model_name, revision=revision)
        print("Model loaded.")
