"""Build an offline blinded reviewer packet without changing the original workbook."""
import html
import json
import zipfile
from collections import defaultdict
from pathlib import Path

from experiments.exp031_annotation_intake import PAIRS, TEMPLATE, sha256, read_workbook, validate_rows
from experiments.exp031_prepare_blinded_annotation import RAW, KEY, display_context

PACKET = Path('deliverables/EXP031_Reviewer_Packet.zip')
VIEWER = Path('deliverables/EXP031_Readable_Cases.html')
AUDIT = Path('results/annotation/exp031_materials_audit.json')
GUIDE = Path('docs/exp031_reviewer_guide.md')
PROTOCOL = Path('docs/exp031_semantic_annotation_protocol.md')


def audit_materials():
    key = json.loads(KEY.read_text())
    if key['source_sha256'] != sha256(RAW):
        raise ValueError('Original EXP-029 source hash changed')
    source = {r['example_id']:r for r in (json.loads(line) for line in RAW.read_text().splitlines())}
    pairs = [json.loads(line) for line in PAIRS.read_text().splitlines()]
    if set(key['mapping']) != {p['case_id'] for p in pairs}:
        raise ValueError('Blind mapping coverage differs')
    for pair in pairs:
        row = source[int(pair['case_id'].split('-')[-1])]
        if pair['question'] != row['question'] or pair['benchmark_reference_answer'] != row['true_answer']:
            raise ValueError('Blinded question/reference differs from raw')
        mapping = key['mapping'][pair['case_id']]
        if set(mapping) != {'A','B'} or set(mapping.values()) != {'S1','S3'}:
            raise ValueError('Invalid arm mapping')
        for arm in ('A','B'):
            system = mapping[arm]
            response = row['s1_prediction' if system == 'S1' else 's3_prediction']
            context = row['original_documents' if system == 'S1' else 's3_generation_documents']
            if pair['response_'+arm] != response or pair['context_'+arm] != display_context(context):
                raise ValueError('Blinded response/context differs from raw')
    report, _ = validate_rows(read_workbook(TEMPLATE))
    if report['status'] != 'UNLABELED_TEMPLATE':
        raise ValueError('Do not distribute a modified or labeled template')
    grouped = defaultdict(list)
    for pair in pairs:
        grouped[' '.join(pair['question'].casefold().split())].append(pair['case_id'])
    audit = {'experiment_id':'EXP-031','status':'materials_verified_no_human_labels',
             'pairs':len(pairs),'responses':len(pairs)*2,'human_label_cells_filled':0,
             'original_responses_and_delivered_contexts_verified':True,
             'workbook_source_cells_verified':True,
             'normalized_duplicate_question_groups':[ids for ids in grouped.values() if len(ids)>1],
             'system_key_in_reviewer_packet':False,
             'source_sha256':{str(p):sha256(p) for p in (RAW,PAIRS,TEMPLATE,PROTOCOL,GUIDE)},
             'scope':'Material integrity only; no semantic labels, agreement, p-values, or effectiveness estimates.'}
    return pairs, audit


def render_html(pairs):
    def esc(text):
        return html.escape(text if isinstance(text,str) else json.dumps(text,ensure_ascii=False))
    sections = []
    for pair in pairs:
        arms = []
        for arm in ('A','B'):
            arms.append(f'<article data-arm="{arm}"><h3>Response {arm}</h3><div class="text">{esc(pair["response_"+arm])}</div>'
                        f'<details><summary>Delivered context {arm} (expand to read)</summary><div class="text">{esc(pair["context_"+arm])}</div></details></article>')
        sections.append(f'<details class="case" id="{esc(pair["case_id"])}"><summary>{esc(pair["case_id"])} — {esc(pair["question"])}</summary>'
                        f'<p><strong>Benchmark reference (not independently verified):</strong> {esc(pair["benchmark_reference_answer"])}</p>'
                        f'<div class="arms">{"".join(arms)}</div></details>')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EXP-031 Blinded Responses</title><style>
body{font:17px/1.55 system-ui,sans-serif;margin:2rem auto;padding:0 1rem;max-width:1400px;color:#182735;background:#f7f8fa}
h1{font-size:1.8rem}summary{cursor:pointer;font-weight:600;padding:.65rem}.case{background:white;border:1px solid #ccd4dc;border-radius:6px;margin:.7rem 0;padding:.5rem}
.arms{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem}article{min-width:0;padding:1rem;border:1px solid #e0e5ea}.text{white-space:pre-wrap;overflow-wrap:anywhere}p{padding:0 .6rem}
@media(max-width:850px){.arms{grid-template-columns:1fr}} </style><main>
<h1>EXP-031 Blinded Responses</h1><p>Read full evidence here and record labels in your personal Excel copy. This page does not collect or save labels.</p>
<p>100 cases, 200 responses. Expand each case and each delivered context. Search using your browser's Find command. Consult the enclosed reviewer guide and codebook.</p>
''' + '\n'.join(sections) + '</main></html>\n'


def main():
    if any(p.exists() for p in (PACKET,VIEWER,AUDIT)):
        raise FileExistsError('Reviewer artifacts already exist; no overwrite')
    pairs, audit = audit_materials()
    with VIEWER.open('x',encoding='utf-8') as handle:
        handle.write(render_html(pairs))
    files = {TEMPLATE.name:TEMPLATE, VIEWER.name:VIEWER, GUIDE.name:GUIDE, PROTOCOL.name:PROTOCOL}
    with zipfile.ZipFile(PACKET,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,path in files.items():
            archive.write(path,arcname=name)
    with zipfile.ZipFile(PACKET) as archive:
        if set(archive.namelist()) != set(files):
            raise ValueError('Unexpected packet member')
        for name,path in files.items():
            if archive.read(name) != path.read_bytes():
                raise ValueError('Packet payload differs from original')
    audit['packet_sha256']=sha256(PACKET)
    audit['viewer_sha256']=sha256(VIEWER)
    with AUDIT.open('x',encoding='utf-8') as handle:
        json.dump(audit,handle,indent=2); handle.write('\n')
    print(json.dumps({k:v for k,v in audit.items() if k!='source_sha256'},indent=2))


if __name__=='__main__':
    main()
