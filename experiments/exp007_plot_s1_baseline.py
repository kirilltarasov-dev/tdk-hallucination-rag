import json
from pathlib import Path

import matplotlib.pyplot as plt


INPUT_PATH = Path(
    "results/processed/exp006_rgb_rescored_summary.json"
)

OUTPUT_PATH = Path(
    "results/figures/exp007_s1_rgb_noise_curve.png"
)


def main():
    with INPUT_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    results = data["results"]

    # 100% noise is rejection accuracy rather than ordinary answer accuracy,
    # so we plot 0-80% as the main accuracy curve.
    answer_results = [
        result
        for result in results
        if result["noise_rate"] < 1.0
    ]

    noise_percent = [
        result["noise_rate"] * 100
        for result in answer_results
    ]

    scores_percent = [
        result["score"] * 100
        for result in answer_results
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))

    plt.plot(
        noise_percent,
        scores_percent,
        marker="o",
        linewidth=2,
    )

    for x, y in zip(noise_percent, scores_percent):
        plt.annotate(
            f"{y:.2f}%",
            (x, y),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
        )

    plt.xlabel("Retrieval Noise (%)")
    plt.ylabel("RGB Answer Accuracy (%)")

    plt.title(
        "Standard RAG Robustness under Retrieval Noise\n"
        "Mistral-7B-Instruct-v0.3 4-bit | RGB en_refine"
    )

    plt.xticks(noise_percent)
    plt.ylim(85, 101)

    plt.grid(alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        OUTPUT_PATH,
        dpi=300,
        bbox_inches="tight",
    )

    print("Saved figure:")
    print(OUTPUT_PATH)

    # 100% noise is a separate Negative Rejection condition.
    rejection = next(
        result
        for result in results
        if result["noise_rate"] == 1.0
    )

    print()
    print("100% noise / Negative Rejection:")
    print(
        f"{rejection['new_correct']}/{rejection['total']} "
        f"= {rejection['score']:.2%}"
    )


if __name__ == "__main__":
    main()