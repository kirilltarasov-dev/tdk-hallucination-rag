"""Draw the implemented candidate, without model inference or result claims."""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def build():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11.5,
                         'svg.fonttype': 'none'})
    fig, ax = plt.subplots(figsize=(8.2, 7.1))
    fig.subplots_adjust(left=.025, right=.975, top=.98, bottom=.02)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis('off')

    def box(x, y, width, height, text, color='#edf2f7'):
        ax.add_patch(FancyBboxPatch((x-width/2, y-height/2), width, height,
                     boxstyle='round,pad=0.009,rounding_size=0.012',
                     linewidth=1, edgecolor='#44546a', facecolor=color))
        ax.text(x, y, text, ha='center', va='center', linespacing=1.3)

    def arrow(a, b, via=None):
        if via:
            points = [a, *via, b]
            ax.plot(*zip(*points[:-1]), color='#44546a', linewidth=1.2)
            a = points[-2]
        ax.annotate('', xy=b, xytext=a,
                    arrowprops={'arrowstyle': '-|>', 'lw': 1.2, 'color': '#44546a'})

    box(.50, .935, .80, .085, 'Question and five supplied passages\nControlled event and year statements')
    box(.50, .795, .50, .085, 'S1 generation\nOne unchanged draft shared by all arms')
    arrow((.50, .883), (.50, .847))
    box(.255, .625, .41, .12, 'V3 neural extraction\nQuestion, passages and draft\nQuestion, facts and answer fields')
    box(.745, .625, .41, .12, 'Independent answer parser\nQuestion and draft only\nFinite grammar and full-text coverage')
    arrow((.44, .743), (.255, .695), via=[(.255, .743)])
    arrow((.56, .743), (.745, .695), via=[(.745, .743)])
    arrow((.09, .935), (.045, .625), via=[(.015, .935), (.015, .625)])
    ax.text(.035, .81, 'Passages', rotation=90, va='center', fontsize=9)
    box(.255, .43, .41, .12, 'Validate the original extraction\nJSON, types and literal spans\nInvalid output remains UNKNOWN', '#f5f5f5')
    arrow((.255, .556), (.255, .50))
    box(.50, .24, .72, .14, 'Compose the independently parsed answer claim\nCheck question agreement, source polarity and coverage\nApply event/year matching, conflict and answer rules', '#f5f5f5')
    arrow((.255, .361), (.34, .319), via=[(.255, .335), (.34, .335)])
    arrow((.745, .556), (.69, .319), via=[(.745, .34), (.69, .34)])
    arrow((.015, .625), (.045, .43), via=[(.015, .43)])
    arrow((.015, .43), (.131, .24), via=[(.015, .24)])
    ax.text(.035, .30, 'Full sources', rotation=90, va='center', fontsize=9)
    box(.50, .072, .86, .10, 'VERIFIED: release the original draft\nREFUTED / CONFLICT / UNKNOWN: canonical abstention')
    arrow((.50, .161), (.50, .131))
    directory = Path('results/figures')
    directory.mkdir(parents=True, exist_ok=True)
    for extension in ('svg', 'png'):
        target = directory / f'candidate_verifier_architecture.{extension}'
        fig.savefig(target, dpi=250, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    build()
