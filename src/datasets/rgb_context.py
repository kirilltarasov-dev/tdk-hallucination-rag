import math
import random

from src.datasets.rgb_loader import RGBExample, load_rgb


def build_rgb_context(
    example: RGBExample,
    noise_rate: float,
    passage_num: int = 5,
) -> list[str]:
    """Build context following the RGB en_refine evaluation protocol."""

    if not 0.0 <= noise_rate <= 1.0:
        raise ValueError("noise_rate must be between 0 and 1")

    if passage_num <= 0:
        raise ValueError("passage_num must be greater than 0")

    neg_num = math.ceil(passage_num * noise_rate)
    pos_num = passage_num - neg_num

    if noise_rate == 1.0:
        neg_num = passage_num
        pos_num = 0
    else:
        if neg_num > len(example.negative_documents):
            neg_num = len(example.negative_documents)
            pos_num = passage_num - neg_num
        elif pos_num > len(example.positive_documents):
            pos_num = len(example.positive_documents)
            neg_num = passage_num - pos_num

    positive = example.positive_documents[:pos_num]
    negative = example.negative_documents[:neg_num]

    docs = positive + negative

    rng = random.Random(2333)
    rng.shuffle(docs)

    return docs


if __name__ == "__main__":
    dataset = load_rgb("data/rgb/en_refine.json")
    example = dataset[0]

    for noise_rate in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        context = build_rgb_context(
            example,
            noise_rate=noise_rate,
            passage_num=5,
        )

        expected_noise = math.ceil(5 * noise_rate)

        print(
            f"noise_rate={noise_rate:.1f} | "
            f"documents={len(context)} | "
            f"expected_noise={expected_noise}"
        )

    # Reproducibility check
    context_a = build_rgb_context(example, noise_rate=0.6)
    context_b = build_rgb_context(example, noise_rate=0.6)

    assert context_a == context_b

    print("\nReproducibility check: PASSED")