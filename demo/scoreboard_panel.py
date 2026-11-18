"""Read-only scoreboard UI; population filters never combine origins."""
from html import escape
import os
import json
import sqlite3
from collections import Counter

import streamlit as st

from src.arena.entry import qr_svg, validate_url
from src.arena.scoreboard import Ledger, summarize

LABELS={'Live demonstration':'live_demo','Archived demo examples':'archived_demo',
        'Software simulations (not observations)':'software_simulation'}


def render_scoreboard():
    st.title('Arena round ledger')
    st.caption('Counts from recorded demonstration rounds · no attack success or efficacy estimate')
    selected=st.selectbox('Record population',list(LABELS))
    kind=LABELS[selected]
    st.button('Refresh ledger')
    try:
        ledger=Ledger()
        export=ledger.export_jsonl(kind)
        snapshot=[json.loads(line) for line in export.splitlines()]
        records=[entry['round'] for entry in snapshot if entry['round'] is not None]
        attempts=[entry['attempt'] for entry in snapshot]
    except (ValueError,OSError,sqlite3.Error) as exc:
        st.error(f'Ledger could not be loaded: {exc}')
        st.stop()
    if kind=='software_simulation':
        st.warning('Software test records only. These are not model measurements.')
    elif kind=='archived_demo':
        st.info('Previously completed engineering examples. Importing them does not create new model observations.')
    counts=Counter(a['state'] for a in attempts)
    evaluation=[r for r in records if r['task']=='evaluation']
    proposals=[r for r in records if r['task']=='proposal']
    cols=st.columns(4)
    for col,label,value in zip(cols,('Completed evaluation rounds','AI proposals','Failed / interrupted','Admission rejections'),
                               (len(evaluation),len(proposals),counts['FAILED']+counts['INTERRUPTED'],counts['DENIED'])):
        col.metric(label,value)
    st.caption(f'Active admissions: {counts["RUNNING"]}. Each evaluation contributes one outcome per system. '
               'Proposals and infrastructure failures do not become answer errors.')
    origins=['All attack origins',*sorted({r['attack_type'] for r in evaluation})]
    attack=st.selectbox('Attack origin filter',origins)
    filtered=[r for r in evaluation if attack==origins[0] or r['attack_type']==attack]
    rows=summarize(filtered)
    if rows:
        headings=('Attack origin','System','Rounds','CORRECT','WRONG','ABSTAIN','UNSCORABLE')
        header=''.join(f'<th>{h}</th>' for h in headings)
        body=''.join('<tr>'+''.join(f'<td>{escape(str(row[h]))}</td>' for h in headings)+'</tr>' for row in rows)
        st.markdown('<div style="overflow-x:auto"><table class="ledger-counts"><thead><tr>'+header+
                    '</tr></thead><tbody>'+body+'</tbody></table></div>',unsafe_allow_html=True)
    else:
        st.info('No completed evaluation rounds in this selection.')
    st.caption('Strict scores use the authored fictional reference. UNSCORABLE is retained explicitly. '
               'Attack origin describes how editing started, not a validated attack taxonomy. '
               'Self-selected repeated demo questions are not independent evaluation data.')
    if attempts:
        with st.expander('Attempts, failures and run identifiers'):
            st.dataframe([{'Run ID':a['id'],'Task':a['task'],'State':a['state'],
                           'Error':a['error'] or ''} for a in attempts],hide_index=True,width='stretch')
    st.download_button('Export population as JSONL',export,
                       file_name=f'arena_{kind}.jsonl',mime='application/x-ndjson',on_click='ignore')
    st.caption('Export includes all attempts in the selected population, their full completed payloads '
               'when available, exact scores and origin. The attack filter changes only the table.')
    st.divider()
    st.subheader('Participant entry')
    url=os.environ.get('TDK_ARENA_PUBLIC_URL','http://127.0.0.1:8501')
    try:
        validate_url(url)
        svg=qr_svg(url)
    except (ValueError,ImportError) as exc:
        st.error(f'Entry link configuration: {exc}')
        return
    st.link_button('Open Arena entry',url)
    st.image(svg,width=220)
    st.download_button('Download entry QR',svg,file_name='arena_entry.svg',mime='image/svg+xml',on_click='ignore')
    if 'TDK_ARENA_PUBLIC_URL' not in os.environ:
        st.caption('Local entry only: this address works on this computer. Scanning it on a phone '
                   'does not connect to this host. An organizer must configure a reachable audience URL.')
    else:
        st.caption('Organizer-configured entry address. Network reachability and phone access must be checked '
                   'at the venue; generating this QR does not publish the app.')
    st.caption('Sessions receive anonymous IDs, not authenticated accounts. Limits: six requests per '
               'session per ten minutes, thirty globally per hour, one model request at a time.')
