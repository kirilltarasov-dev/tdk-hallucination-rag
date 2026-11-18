"""Streamlit editor for one inserted source; edits never invoke inference."""
import copy

import streamlit as st

from src.arena.attacks import TEMPLATES, insert_passage, template_text
from src.arena.client import run_local


def render_editor(base):
    case = copy.deepcopy(base)
    key = f'attack_{base["case_id"]}_'
    with st.expander('Attack editor', expanded=False):
        st.caption('Insert one adversarial passage while retaining the original sources. '
                   'Edits create demo inputs, never changes to the recorded experiment. '
                   'Ordinal, numeric and correction language may exceed the verifier grammar.')
        enabled = st.toggle('Insert an attack passage', key=key + 'enabled')
        if not enabled:
            return case, None
        kind = st.selectbox('Attack template', TEMPLATES, key=key + 'template')
        load, ai = st.columns(2)
        if load.button('Load template into editor', key=key + 'load', width='stretch'):
            st.session_state[key + 'text'] = template_text(kind, base['question'], base['documents'])
            st.session_state[key + 'origin'] = kind
            st.session_state[key + 'proposal'] = None
        if ai.button('Ask local AI for an attack', key=key + 'ai', width='stretch'):
            try:
                with st.spinner('Generating one editable attack proposal…'):
                    payload = run_local(base['question'], base['documents'], attacker=True)
                st.session_state[key + 'text'] = payload['result']['proposal']
                st.session_state[key + 'origin'] = 'AI proposal'
                st.session_state[key + 'proposal'] = payload['run_id']
                st.session_state[key + 'proposal_path'] = payload['saved_directory']
            except (RuntimeError, ValueError, OSError) as exc:
                st.error(f'AI proposal did not complete: {exc}')
        st.caption('AI suggestion: one optional local call, up to 256 output tokens. '
                   'It sees the question and original sources; it does not run the three systems.')
        text = st.text_area('Attack passage', key=key + 'text', height=120,
                            help='Free text; templates and AI output remain editable. Maximum 2,000 characters.')
        position = st.selectbox('Insertion position', range(len(base['documents']) + 1),
                                format_func=lambda index: f'{index + 1} of {len(base["documents"]) + 1}',
                                key=key + 'position')
        st.caption('Commit a text edit with Ctrl+Enter / ⌘+Enter or by leaving the field. '
                   'The sources below show the exact current evaluation input. '
                   'Disable insertion to restore the original context.')
        proposal_id = st.session_state.get(key + 'proposal')
        if proposal_id:
            st.caption(f'Editable AI proposal {proposal_id[:12]} · '
                       f'{st.session_state[key + "proposal_path"]}')
        try:
            case['documents'], provenance = insert_passage(
                base['question'], base['documents'], text, position,
                st.session_state.get(key + 'origin', 'Free text'), proposal_id)
        except ValueError as exc:
            st.warning(str(exc))
            st.stop()
        st.caption(f'Inserted source {provenance["source_id"]} · current input '
                   f'{provenance["input_hash"][:12]}. Previous answers only appear if their inputs match.')
        return case, provenance
