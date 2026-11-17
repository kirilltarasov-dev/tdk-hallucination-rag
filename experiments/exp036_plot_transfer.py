"""Plot measured EXP-036 counts; no confidence or population claims."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SUMMARY = Path('results/processed/exp036_prospective_transfer_summary.json')
OUTPUT = Path('results/figures/exp036_verification_tradeoff.png')


def main():
    if OUTPUT.exists():
        raise FileExistsError('Figure already exists; preserve the recorded artifact')
    result = json.loads(SUMMARY.read_text())
    arms = ['core', 'predicate_guard', 'combined']
    labels = ['Core', '+ Predicate\nguard', '+ Answer\nguard']
    colors = ['#52657b', '#397b8e', '#b2693c']
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 4.2), sharey=True)
    for ax, key, title in zip(axes, ['false_confirmations','correct_decisive','unknown'],
                              ['Unsupported confirmations', 'Correct decisive verdicts', 'UNKNOWN verdicts']):
        values = [result['primary_metrics'][a][key] for a in arms]
        bars = ax.bar(labels, values, color=colors, width=.65)
        ax.bar_label(bars, padding=4, fontsize=11)
        ax.set_title(title, fontsize=11)
        ax.set_ylim(0,45)
        ax.set_yticks([0,15,30,45])
        ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='y', alpha=.18)
        ax.set_axisbelow(True)
    axes[0].set_ylabel('Cases (primary n = 45)')
    fig.suptitle('EXP-036: fewer false confirmations, fewer useful decisions', fontsize=14)
    fig.text(.5,.035, '48 authored synthetic cases: 45 primary + 3 false-source controls (all still VERIFIED).\nSame neural extraction in all arms. Correct-decision retention: 18/24 = 75%; target: 80%.',
             ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.13,1,.93])
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(OUTPUT,dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
