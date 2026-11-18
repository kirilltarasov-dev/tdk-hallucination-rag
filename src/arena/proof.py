"""Read-only proof presentation derived from a replay-validated candidate trace."""
from html import escape
import json

from src.verification.independent_answer import verify_saved_extraction
from src.verification.symbolic_rules import EvidenceFact, QuestionFrame, _matches_question

COLORS = {'VERIFIED':'#176b5b', 'REFUTED':'#a43d32', 'CONFLICT':'#925614', 'UNKNOWN':'#596579'}


def proof_view(question, documents, draft, raw, trace):
    replay = verify_saved_extraction(question, documents, draft, raw)
    if replay != trace:
        raise ValueError('Proof trace differs from replay of these inputs')
    independent = trace['independent_answer']
    source = trace['source_trace']
    answer = trace['answer_trace']
    decision = trace['decision']
    checks = [
        {'stage':'Independent draft parse', 'status':independent['status'], 'detail':independent['reason']},
        {'stage':'Extraction schema and quotations', 'status':'BLOCKED' if trace['validation_error'] else 'PASSED',
         'detail':trace['validation_error'] or 'Complete extraction passed the strict parser.'},
        {'stage':'Compose independent answer', 'status':'APPLIED' if trace['replacement_applied'] else 'NOT APPLIED',
         'detail':'Preserved neural question and facts; substituted the text-only answer.' if trace['replacement_applied']
                  else 'No substitution; see the terminating rule and earlier stage outcomes.'},
        {'stage':'Full-source audit', 'status':source['status'] if source else 'NOT REACHED',
         'detail':source['decision']['rule_id'] if source else 'Stopped before source audit.'},
        {'stage':'Full-answer audit', 'status':answer['status'] if answer else 'NOT REACHED',
         'detail':answer['decision']['rule_id'] if answer else 'Stopped before answer audit.'},
        {'stage':'Final decision', 'status':decision['verdict'], 'detail':decision['rule_id']},
    ]
    audited = {check['source_id']:check for check in source['source_checks']} if source else {}
    facts = trace['preserved_facts'] or []
    witnesses = decision['matching_facts']
    frame = trace['preserved_question']
    fact_nodes = []
    for i, fact in enumerate(facts):
        fact_nodes.append({'id':f'f{i}', **fact, 'witness':fact in witnesses,
                           'target_match':bool(frame and _matches_question(QuestionFrame(**frame), EvidenceFact(**fact)))})
    sources = []
    for source_id, text in documents.items():
        check = audited.get(source_id)
        status = ('PASSED' if check['matched'] else 'BLOCKED') if check else 'NOT REACHED'
        spans = [f['source_span'] for f in witnesses if f['source_id']==source_id]
        reason = 'Rule witness' if spans else None
        error = trace['validation_error']
        diagnostic = bool(error and error.startswith(source_id + '.'))
        if check and not check['matched']:
            reason = 'Blocking source audit'
        elif diagnostic:
            reason = 'Extraction diagnostic; source is not declared false'
        # A polarity conflict emits no matching_facts. Link the audited statements
        # that explicitly affirm and deny the same target value, without adding facts.
        if decision['rule_id'] == 'G4_POSITIVE_NEGATIVE_CONFLICT' and check and check['statement']:
            statement = check['statement']
            def same_target(other):
                return (other and frame and other['year']==frame['year']
                        and other['event'].casefold()==frame['event'].casefold())
            if same_target(statement) and any(same_target(c['statement'])
                    and c['statement']['value'].casefold()==statement['value'].casefold()
                    and c['statement']['polarity'] != statement['polarity'] for c in audited.values()):
                spans = [text]
                reason = 'Affirmed and denied target win in source audit'
        sources.append({'source_id':source_id, 'text':text, 'audit_status':status,
                        'statement':check['statement'] if check else None,
                        'highlights':spans, 'reason':reason,
                        'highlight_full':bool(diagnostic or (check and not check['matched']))})
    return {'question':question, 'draft':draft, 'question_frame':frame,
            'independent_answer':independent, 'decision':decision, 'checks':checks,
            'sources':sources, 'facts':fact_nodes, 'factual_truth_verified':False}


def highlighted_text(text, spans, whole=False):
    """Escape all untrusted text; highlight exact, merged quotation intervals."""
    intervals = []
    if whole:
        intervals = [(0,len(text))]
    else:
        for span in spans:
            if not span or span not in text:
                raise ValueError('Highlight quotation is absent from source')
            start = 0
            while (start := text.find(span,start)) != -1:
                intervals.append((start,start+len(span)))
                start += len(span)
    merged = []
    for start,end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0],max(end,merged[-1][1]))
        else:
            merged.append((start,end))
    output, offset = [], 0
    for start,end in merged:
        output.extend((escape(text[offset:start]), '<mark>', escape(text[start:end]), '</mark>'))
        offset = end
    output.append(escape(text[offset:]))
    return ''.join(output)


def graph_dot(view):
    """DOT with fixed node IDs and quoted user labels; no external resource URLs."""
    lines = ['digraph proof {', 'rankdir=LR;', 'graph [bgcolor="transparent"];',
             'node [shape=box, style="rounded,filled", fillcolor="#f1f5f4", fontname="Arial"];',
             'edge [fontname="Arial", fontsize=10, color="#6b827e"];']
    def node(key,label,color='#f1f5f4'):
        lines.append(f'{key} [label={json.dumps(label,ensure_ascii=False)}, fillcolor="{color}"];')
    def edge(left,right,label,style='solid'):
        lines.append(f'{left} -> {right} [label={json.dumps(label)}, style="{style}"];')
    frame = view['question_frame']
    node('target', 'NEURAL QUESTION FRAME\n'+(f'{frame["event"]} · {frame["year"]}' if frame else 'Not validated'))
    claim = view['independent_answer']
    node('draft', f'INDEPENDENT DRAFT CLAIM\n{claim["value"] or claim["status"]}')
    decision = view['decision']
    node('decision', f'{decision["verdict"]}\n{decision["rule_id"]}', '#e4ede9' if decision['verdict']=='VERIFIED' else '#f5e6dd')
    edge('draft','decision','checked draft')
    edge('target','decision','question frame', 'dashed')
    for index, source in enumerate(view['sources']):
        key = f's{index}'
        node(key, f'SOURCE {source["source_id"]}\nAudit: {source["audit_status"]}',
             '#ffe5b4' if source['reason'] else '#f1f5f4')
        extracted = [f for f in view['facts'] if f['source_id']==source['source_id']]
        for fact in extracted:
            node(fact['id'], f'NEURAL FACT\n{fact["value"]} won\n{fact["event"]} · {fact["year"]}',
                 '#ffe5b4' if fact['witness'] else '#f1f5f4')
            edge(key,fact['id'],'quoted from')
            edge(fact['id'],'target','target match' if fact['target_match'] else 'outside target',
                 'solid' if fact['target_match'] else 'dashed')
            if fact['witness']:
                edge(fact['id'],'decision','rule witness')
        parsed = source['statement']
        if parsed and parsed['polarity']==-1:
            node(f'n{index}',f'AUDITED NEGATION\n{parsed["value"]} did not win\n{parsed["event"]} · {parsed["year"]}')
            edge(key,f'n{index}','deterministic audit')
        elif not extracted:
            node(f'e{index}','No validated neural fact')
            edge(key,f'e{index}','extraction state','dashed')
    return '\n'.join([*lines,'}'])
