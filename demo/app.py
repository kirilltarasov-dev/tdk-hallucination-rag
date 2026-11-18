"""Arena M1/M2: recorded exploration and explicit local three-system runs."""
from html import escape
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from src.arena.replay import FAMILIES, export_challenge, load_challenges
from src.arena.client import decorate_live_case, export_live_case, run_local
from src.arena.live import input_hash

st.set_page_config(page_title='RAG Red-Team Arena', page_icon='◈', layout='wide')

st.markdown('''<style>
.block-container {max-width:1320px;padding-top:4.3rem;padding-bottom:3rem;}
[data-testid="stSidebar"] {border-right:1px solid #dce4e5;}
h1 {font-size:2.05rem!important;letter-spacing:-.06rem;line-height:1.16!important;}
h2 {font-size:1.25rem!important;letter-spacing:-.02rem;}
h3 {font-size:1.07rem!important;}
.eyebrow {font-size:.68rem;font-weight:750;letter-spacing:.14rem;color:#507079;}
.brand {font-size:1.65rem;line-height:1.1;font-weight:800;letter-spacing:-.05rem;margin:.6rem 0 1.2rem;}
.pill {display:inline-block;border-radius:6px;padding:4px 9px;font-size:.7rem;
font-weight:750;letter-spacing:.045rem;background:#e8efee;color:#176b5b;}
.hero {background:#173c3d;color:#fff;padding:23px 27px;border-radius:13px;margin:14px 0 18px;}
.hero .eyebrow {color:#abd1c5;}.hero .question {font-size:1.45rem;font-weight:650;
line-height:1.4;margin:9px 0 4px;overflow-wrap:anywhere;}
.hero .context {font-size:.8rem;color:#c7dbd6;}
.source {background:#fff;border:1px solid #dce5e5;border-left:3px solid #759e98;
border-radius:9px;padding:15px 18px;margin:8px 0;}
.source .source-id {font-size:.68rem;letter-spacing:.08rem;font-weight:750;color:#526e77;}
.source p {margin:7px 0 0;font-size:.96rem;line-height:1.55;overflow-wrap:anywhere;}
.answer-card {background:white;border:1px solid #dce5e5;border-radius:11px;
padding:20px;min-height:247px;display:flex;flex-direction:column;}
.answer-card.candidate {border:2px solid #176b5b;padding:19px;}
.answer-card .name {font-size:.78rem;font-weight:750;color:#48616b;margin-bottom:12px;}
.answer-card .answer {font-size:1.03rem;line-height:1.5;font-weight:600;flex:1;
overflow-wrap:anywhere;white-space:pre-wrap;margin:14px 0;}
.answer-card .measurement {border-top:1px solid #edf1f2;padding-top:11px;
font-size:.71rem;color:#59717a;line-height:1.6;}
.score {font-size:.69rem;font-weight:750;letter-spacing:.025rem;margin-bottom:6px;}
.correct {color:#176b5b;}.wrong {color:#b13d39;}.muted {color:#6d7782;}
.notice {padding:15px 19px;border-radius:9px;font-size:.9rem;line-height:1.5;margin:12px 0;}
.notice.fail {background:#fff0ed;border:1px solid #edc4bd;color:#863d32;}
.notice.info {background:#edf5f3;border:1px solid #cde1db;color:#284f47;}
.trace-step {padding:13px 15px;border-radius:8px;border:1px solid #dce5e5;background:#fff;
min-height:104px;margin:5px 0 10px;overflow-wrap:anywhere;}
.trace-step .label {font-size:.67rem;letter-spacing:.06rem;color:#617681;font-weight:700;}
.trace-step .value {font-size:.94rem;font-weight:650;margin-top:8px;}
.trace-step .note {font-size:.74rem;color:#617681;margin-top:3px;}
.reference {background:#fff;border:1px dashed #afc3c3;padding:15px 18px;border-radius:9px;margin-top:8px;}
.reference .value {font-weight:700;font-size:1.04rem;margin-top:6px;}
.scope {font-size:.8rem;line-height:1.6;color:#5c7078;}
@media(max-width:700px){.block-container{padding:4.2rem 1rem 1rem;}.hero{padding:18px;}
.hero .question{font-size:1.18rem;}.answer-card{min-height:205px;}h1{font-size:1.7rem!important;}}
</style>''', unsafe_allow_html=True)


try:
    challenges = load_challenges()
except (OSError, ValueError, KeyError) as exc:
    st.error(f'Recorded data could not be verified: {exc}')
    st.stop()

by_id = {case['case_id']: case for case in challenges}


def choose(case_id):
    st.session_state['family_filter'] = 'All cases'
    st.session_state['challenge_id'] = case_id


def step(offset, options):
    index = options.index(st.session_state['challenge_id'])
    st.session_state['challenge_id'] = options[(index + offset) % len(options)]


with st.sidebar:
    st.markdown('<div class="eyebrow">UNIVERSITY OF DEBRECEN · TDK</div>'
                '<div class="brand">RAG<br>Red-Team Arena</div>'
                '<span class="pill">LOCAL RESEARCH DEMONSTRATOR</span>', unsafe_allow_html=True)
    st.write('')
    mode = st.radio('Mode', ['Recorded experiment', 'Live local run'], key='arena_mode')
    live_mode = mode == 'Live local run'
    selected_family = st.selectbox('Source scenario', ['All cases', *FAMILIES.values()],
                                   key='family_filter')
    visible = [case for case in challenges if selected_family == 'All cases'
               or case['family_label'] == selected_family]
    ids = [case['case_id'] for case in visible]
    if 'challenge_id' not in st.session_state:
        st.session_state['challenge_id'] = 'E044-005'
    if st.session_state['challenge_id'] not in ids:
        st.session_state['challenge_id'] = ids[0]
    selected_id = st.selectbox('Challenge', ids, key='challenge_id',
                               format_func=lambda item: f'{item} · {by_id[item]["question"]}')
    previous, following = st.columns(2)
    previous.button('Previous', on_click=step, args=(-1, ids), width='stretch')
    following.button('Next', on_click=step, args=(1, ids), width='stretch')
    st.caption(f'{len(visible)} of 24 recorded challenges')
    show_reference = st.toggle('Reveal fictional reference', value=True)
    st.divider()
    st.markdown('**How to read the verdict**')
    st.markdown('<div class="scope">VERIFIED means the draft agrees with the supplied '
                'sources within the supported language. It does not establish that '
                'those sources are true.</div>', unsafe_allow_html=True)
    st.divider()
    st.caption('Recorded EXP-044 · 18 November 2026\n\n'
               '24 fictional questions · 6 scenarios\n\n'
               'Supplied passages · no live retrieval\n\n'
               'Live generation starts only when you press Run.')

case = by_id[selected_id]

st.markdown('<div class="eyebrow">FROM MODEL ANSWER TO AUDITABLE DECISION</div>', unsafe_allow_html=True)
st.title('Run three verification approaches' if live_mode else 'Explore what verification catches')
st.caption('Generate a shared draft, compare two checks, and inspect the source decision.' if live_mode else
           'Compare saved answers, inspect the evidence, and see where source consistency stops.')

shortcut_columns = st.columns(3)
for column, label, identity in zip(shortcut_columns,
                                  ('Paraphrase example' if live_mode else 'Recovered answer', 'Source conflict', 'False source'),
                                  ('E044-005', 'E044-013', 'E044-021')):
    column.button(label, on_click=choose, args=(identity,), width='stretch')

st.markdown(f'<div class="hero"><div class="eyebrow">{escape(case["case_id"])} · '
            f'{escape(case["family_label"].upper())}</div><div class="question">'
            f'{escape(case["question"])}</div><div class="context">'
            f'{"Local generation" if live_mode else "Recorded replay"} · '
            f'{len(case["documents"])} supplied passage(s) · shared initial draft</div></div>',
            unsafe_allow_html=True)

evidence, reference = st.columns([2.05, 1])
with evidence:
    st.subheader('Sources seen by the model')
    for source_id, text in case['documents'].items():
        st.markdown(f'<div class="source"><div class="source-id">{escape(source_id)}</div>'
                    f'<p>{escape(text)}</p></div>', unsafe_allow_html=True)
with reference:
    st.subheader('Reference for this case')
    if show_reference:
        st.markdown('<div class="reference"><div class="eyebrow">AUTHORED FICTIONAL WINNER</div>'
                    f'<div class="value">{escape(case["authored_reference"])}</div>'
                    '<div class="scope">Used for evaluation. Never supplied to the model or verifier.</div></div>',
                    unsafe_allow_html=True)
    else:
        st.info('Reference hidden. Reveal it in the sidebar to compare source agreement with correctness.')

if live_mode:
    st.caption('Cached Mistral 7B · 3 local calls · up to 1,280 generated tokens. '
               'S2 is same-model self-review; the NS arm uses the existing symbolic candidate.')
    identity = input_hash(case['question'], case['documents'])
    if 'live_rounds' not in st.session_state:
        st.session_state['live_rounds'] = {}
    if st.button('Run three systems locally', type='primary'):
        try:
            with st.spinner('Generating S1, reviewing with S2, and checking the shared draft…'):
                payload = run_local(case['question'], case['documents'])
            st.session_state['live_rounds'][identity] = payload
        except (RuntimeError, ValueError, OSError) as exc:
            st.error(f'Local run did not complete: {exc}')
            st.stop()
    payload = st.session_state['live_rounds'].get(identity)
    if payload is None:
        st.info('No local run for these inputs in this session. Press Run to generate all three answers.')
        st.caption('Changing the scenario or revealing the reference does not start inference. '
                   'Demonstration rounds are separate from the frozen research experiments.')
        st.stop()
    case = decorate_live_case(case, payload)
    st.caption(f'Local round {payload["run_id"][:12]} · saved in {payload["saved_directory"]}')

candidate = case['systems'][2]
trace = candidate['trace']
decision = trace['decision']
st.subheader('Local run answers' if live_mode else 'Recorded answers')
st.caption('S2 and the neuro-symbolic verifier use the same newly generated S1 draft. '
           'S2 provides a reviewed answer, not a symbolic verdict.' if live_mode else
           'Original NS and Candidate NS verify the same S1 draft. Original NS is not S2 self-review.')
for column, system in zip(st.columns(3), case['systems']):
    with column:
        action = {'DRAFT': 'UNVERIFIED DRAFT', 'RELEASE': 'RELEASED', 'ABSTAIN': 'WITHHELD',
                  'SELF_REVIEWED': 'SELF-REVIEWED'}[system['action']]
        score = system['score']['category']
        score_text = {'CORRECT': 'CORRECT · exact scorer', 'WRONG': 'WRONG · exact scorer',
                      'ABSTAIN': 'ABSTENTION', 'UNSCORABLE': 'UNSCORABLE · outside answer format'}[score]
        score_class = {'CORRECT': 'correct', 'WRONG': 'wrong'}.get(score, 'muted')
        score_html = f'<div class="score {score_class}">{score_text}</div>' if show_reference else ''
        card_class = 'candidate' if system['system_id'] == 'Candidate_NS' else ''
        st.markdown(f'<div class="answer-card {card_class}"><div class="name">'
                    f'{escape(system["name"])}</div><div><span class="pill">{action}</span></div>'
                    f'<div class="answer">{escape(system["answer"])}</div>{score_html}'
                    f'<div class="measurement">Source decision: {escape(system["verdict"] or "not applied")}<br>'
                    f'{"Measured" if live_mode else "Recorded"} {system["latency_seconds"]:.2f} s · {system["calls"]} call(s) · '
                    f'{system["output_tokens"]:,} output tokens</div></div>', unsafe_allow_html=True)

if show_reference and candidate['verdict'] == 'VERIFIED' and candidate['score']['category'] == 'WRONG':
    st.markdown('<div class="notice fail"><strong>Source-consistent, but wrong.</strong> '
                'The verifier accepted this answer because it matches the source. The fictional reference '
                'names a different winner. This is a measured limitation of the current method.</div>',
                unsafe_allow_html=True)
elif candidate['verdict'] == 'CONFLICT':
    st.markdown('<div class="notice info"><strong>The sources disagree.</strong> '
                'The candidate withholds the draft. These sources give it no basis for choosing which '
                'winner is true.</div>', unsafe_allow_html=True)
elif candidate['verdict'] == 'UNKNOWN':
    st.markdown('<div class="notice info"><strong>The candidate cannot establish support.</strong> '
                'It withholds the draft. UNKNOWN is an unresolved decision, not a factual verdict.</div>',
                unsafe_allow_html=True)
elif (not live_mode and show_reference and case['systems'][1]['score']['category'] == 'ABSTAIN'
      and candidate['score']['category'] == 'CORRECT'):
    st.markdown('<div class="notice info"><strong>A correct answer recovered.</strong> '
                'The candidate releases a correct draft that the original NS policy withheld.</div>',
                unsafe_allow_html=True)

st.caption('Times and tokens come from this local round. The S1 call is shared; loading time is excluded. '
           'A demo round does not establish comparative effectiveness.' if live_mode else
           'Times and tokens are historical EXP-044 measurements. The draft call is shared. '
           'The browser is replaying saved outputs, not measuring fresh inference.')

with st.expander('Why the candidate made this decision', expanded=True):
    independent = trace['independent_answer']
    source_audit = trace.get('source_trace')
    audit_status = source_audit['status'] if source_audit else 'NOT REACHED'
    step_values = (
        ('01 · READ THE DRAFT', independent['status'], independent.get('value') or independent['reason']),
        ('02 · CHECK THE SOURCES', audit_status, 'Full-source coverage and polarity audit'),
        ('03 · APPLY THE RULE', decision['verdict'], decision['rule_id']),
    )
    for column, (label, value, note) in zip(st.columns(3), step_values):
        column.markdown(f'<div class="trace-step"><div class="label">{escape(label)}</div>'
                        f'<div class="value">{escape(value)}</div><div class="note">{escape(note)}</div></div>',
                        unsafe_allow_html=True)
    st.write(decision['explanation'])
    matching = decision.get('matching_facts', [])
    if matching:
        st.markdown('**Source quotations used by the fired rule**')
        for fact in matching:
            st.markdown(f'<div class="source"><div class="source-id">{escape(fact["source_id"])} · '
                        f'{escape(fact["event"])} · {fact["year"]}</div>'
                        f'<p>{escape(fact["source_span"])}</p></div>', unsafe_allow_html=True)
    else:
        st.caption('This decision has no matching-fact witness. See the full trace for the blocking check.')
    facts = trace.get('preserved_facts') or []
    if facts:
        st.markdown('**Neural facts retained by the verifier**')
        st.dataframe([{'Source': f['source_id'], 'Relation': f['relation'], 'Event': f['event'],
                       'Year': f['year'], 'Winner': f['value']} for f in facts],
                     hide_index=True, width='stretch')

with st.expander('Raw extraction and full candidate trace'):
    st.caption('Verbatim V3 model output followed by the replayed deterministic trace.')
    st.code(case['raw_record']['calls']['V3']['output'], language='json')
    st.json(trace, expanded=False)

st.download_button('Download this case and full trace',
                   data=export_live_case(case) if live_mode else export_challenge(case),
                   file_name=(f'arena_{selected_id}_{case["live_payload"]["run_id"]}.json' if live_mode else
                              f'arena_{selected_id}_recorded.json'), mime='application/json',
                   width='content')
st.caption('Export includes this round’s prompts and outputs, post-generation exact scores, '
           'the fictional reference and ordered-input fingerprint. Code hashes are in the saved run manifest.'
           if live_mode else 'Export includes all recorded prompts and outputs, original exact scores, '
           'the fictional reference and source hashes.')
st.divider()
st.markdown('**Research scope**')
st.caption('EXP-044 used 24 authored fictional cases. Its candidate-versus-S1 utility screen '
           'was inconclusive because four drafts were outside the frozen answer format. '
           'The app offers recorded M1 exploration and explicit M2 local generation. '
           'Live attack editing and an audience scoreboard remain later milestones.')
