"""Post-run figure of saved answer-status changes; no inference or rescoring."""
import hashlib
import json
from pathlib import Path

SUMMARY=Path('results/processed/exp042_answer_context_invariance_summary.json')
RAW=Path('results/raw/exp042_answer_context_invariance.jsonl')
OUTPUT=Path('results/figures/exp042_answer_context_invariance')


def main():
    summary=json.loads(SUMMARY.read_text())
    if hashlib.sha256(RAW.read_bytes()).hexdigest()!=summary['raw_sha256']:
        raise ValueError('Raw source hash changed')
    if any(OUTPUT.with_suffix(ext).exists() for ext in ('.svg','.png')):
        raise FileExistsError('Do not overwrite figure')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    conditions=('supports','other_winner','wrong_year','explicit_denial')
    codes={'SINGLE_CLAIM':0,'UNRESOLVED':1,'ABSTENTION':2,'UNINSPECTABLE':3}
    labels=('CLAIM','UNRESOLVED','ABSTENTION','INVALID')
    colors=('#0072B2','#E69F00','#CC79A7','#777777')
    fig,axes=plt.subplots(1,2,figsize=(12,4.3),layout='constrained')
    for ax,prompt in zip(axes,('V2','V3')):
        rows=sorted((r for r in summary['identity_results'] if r['prompt_variant']==prompt),key=lambda r:r['identity'])
        values=[[codes[r['signatures'][c][0]] if r['signatures'][c] else 3 for c in conditions] for r in rows]
        ax.imshow(values,cmap=ListedColormap(colors),vmin=-.5,vmax=3.5,aspect='auto')
        for i,row in enumerate(values):
            for j,value in enumerate(row):
                ax.text(j,i,labels[value],ha='center',va='center',fontsize=8,
                        color='white' if value in (0,3) else 'black',weight='bold')
        ax.set_xticks(range(4),['Supports','Other\nwinner','Wrong\nyear','Explicit\ndenial'])
        ax.set_yticks(range(4),['Dawn Herons','Violet Otters','Golden Badgers','Scarlet Swans'])
        ax.set_title(prompt+' extraction prompt',fontsize=12)
        ax.set_xlabel('Source context; question and response remain fixed within each row')
        ax.tick_params(length=0)
        for spine in ax.spines.values():spine.set_visible(False)
    fig.suptitle('EXP-042: The same assertion receives different labels when evidence changes\nExpected: CLAIM in every cell; four authored identities, not a population estimate',fontsize=12)
    fig.legend(handles=[Patch(color=colors[i],label=labels[i]) for i in range(3)],
               loc='outside lower center',ncol=3,frameon=False)
    for ext in ('.png','.svg'):fig.savefig(OUTPUT.with_suffix(ext),dpi=180,bbox_inches='tight')
    plt.close(fig)


if __name__=='__main__':main()
