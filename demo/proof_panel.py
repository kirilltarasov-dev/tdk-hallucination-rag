"""Linked fact graph and trace checklist shared by recorded/live examples."""
from html import escape
import json

import streamlit as st

from src.arena.proof import COLORS, graph_dot, highlighted_text, proof_view
from src.arena.proof_examples import load_proof_examples


def render_proof(question, documents, draft, raw, trace, *, key):
    try:
        view = proof_view(question, documents, draft, raw, trace)
    except ValueError as exc:
        st.error(f'Proof cannot be displayed: {exc}')
        st.stop()
    verdict = view['decision']['verdict']
    st.markdown(f'<div class="proof-verdict" style="border-left:5px solid {COLORS[verdict]};'
                'padding:12px 16px;background:#edf2f1;border-radius:7px">'
                f'<strong>{escape(verdict)}</strong> · {escape(view["decision"]["rule_id"])}</div>',
                unsafe_allow_html=True)
    st.write(view['decision']['explanation'])
    if verdict=='REFUTED':
        st.caption('REFUTED rejects the draft relative to supplied evidence and the unique-winner assumption. '
                   'It does not establish which source is true. A false-abstention rule may also produce this verdict.')
    st.markdown('**Fact and provenance graph**')
    st.graphviz_chart(graph_dot(view), width='stretch')
    st.caption('Neural facts have passed schema and quotation checks; this does not establish their truth. '
               'Gold nodes mark rule witnesses or diagnostic sources. Dashed links mark scope or missing facts. '
               'Audited negations come from deterministic source checks, not neural positive facts.')
    st.markdown('**Executed checks**')
    # Plain HTML keeps statuses readable and independently browser-testable.
    rows = ''.join('<tr>'+''.join(f'<td>{escape(str(row[k]))}</td>' for k in ('stage','status','detail'))+'</tr>'
                   for row in view['checks'])
    st.markdown('<table class="proof-checks"><thead><tr><th>Stage</th><th>Outcome</th><th>Trace detail</th></tr></thead>'
                f'<tbody>{rows}</tbody></table>',unsafe_allow_html=True)
    st.caption('These are trace-backed stage outcomes and emitted rule IDs, not a log of every rule condition. '
               'NOT REACHED and NOT EVALUATED mean no successful check is claimed.')
    st.markdown('**Linked source passages**')
    selected = st.selectbox('Inspect a proof source', ['All sources', *documents], key=key+'_source')
    for source in view['sources']:
        if selected!='All sources' and selected!=source['source_id']:
            continue
        text = highlighted_text(source['text'],source['highlights'],source['highlight_full'])
        st.markdown('<div class="proof-source" style="border:1px solid #dce5e5;border-radius:8px;'
                    'padding:12px 16px;margin:8px 0;overflow-wrap:anywhere">'
                    f'<strong>{escape(source["source_id"])}</strong> · source audit: {source["audit_status"]}'
                    f'<p>{escape(source["reason"] or "No final-rule witness or blocking diagnostic recorded.")}</p>'
                    f'<p>{text}</p></div>',unsafe_allow_html=True)
    st.caption('Highlights identify evidence or diagnostic context. They do not label a passage as factually false.')
    if not view['facts']:
        st.info('No validated neural facts are available in this trace. Raw extraction is retained separately.')
    st.download_button('Download proof graph and checks', json.dumps(
        {'artifact_type':'arena_proof_view','question':question,'documents':documents,'draft':draft,
         'raw_extraction':raw,'candidate_trace':trace,'view':view,'graph_dot':graph_dot(view),
         'scope':'Presentation of replayed source-consistency checks, not external truth.'},indent=2,ensure_ascii=False),
         file_name=f'{key}_proof.json',mime='application/json',key=key+'_download')


def render_examples():
    st.title('Inspect the proof, including its limits')
    st.caption('Saved inputs · deterministic replay · zero new model calls')
    try:
        examples = load_proof_examples()
    except (ValueError, OSError) as exc:
        st.error(f'Proof examples could not be verified: {exc}')
        st.stop()
    by_key = {c['example_id']:c for c in examples}
    selected = st.selectbox('Proof example',list(by_key),format_func=lambda k:by_key[k]['label'])
    case = by_key[selected]
    st.info(case['provenance']['description'])
    st.subheader(case['question'])
    st.markdown('**Saved S1 draft**')
    st.code(case['draft'],language=None)
    render_proof(case['question'],case['documents'],case['draft'],case['raw_extraction'],case['trace'],key=selected)
    with st.expander('Original extraction and replay provenance'):
        st.code(case['raw_extraction'],language='json')
        st.json(case['provenance'])
        st.caption('Pinned source SHA-256: '+case['source_sha256'])
    st.download_button('Download example with provenance',json.dumps(case,indent=2,ensure_ascii=False),
                       file_name=f'{selected}_example.json',mime='application/json')
