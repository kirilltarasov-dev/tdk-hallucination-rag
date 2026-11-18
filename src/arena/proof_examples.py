"""Pinned historical inputs for proof walkthroughs; no generation or new scores."""
import hashlib
import json
from pathlib import Path

from src.arena.proof import proof_view
from src.arena.worker import verify_saved_run
from src.verification.independent_answer import verify_saved_extraction

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL = 'results/raw/exp040_generated_answers.jsonl'
FAILURE = 'results/demo/arena_m3_smoke/0084deabb5bb478488123c78f5af864b/result.json'
PINNED = {HISTORICAL:'a844f72dc19617bbb246761837d822e52d6ad887ca386b3a1c8d38004447d2b5',
          FAILURE:'421bcd897daa7bdbd9b2aca1bbad2d5057e4bfa527e02f14e2d85857a05385b1'}


def load_proof_examples(root=ROOT):
    root = Path(root)
    for relative, expected in PINNED.items():
        if hashlib.sha256((root/relative).read_bytes()).hexdigest()!=expected:
            raise ValueError('Proof example artifact hash mismatch: '+relative)
    rows = [json.loads(line) for line in (root/HISTORICAL).read_text().splitlines()]
    historical = next(r for r in rows if r['case_id']=='E040-018')
    failed = verify_saved_run((root/FAILURE).parent)
    examples = []
    for key, label, record, draft, raw, provenance in (
        ('refuted', 'Answer mismatch · saved EXP-040 draft', historical, historical['answers']['S1'],
         historical['verification']['raw_extraction'],
         {'source':HISTORICAL, 'case_id':'E040-018', 'mode':'retrospective_candidate_replay',
          'description':'Saved EXP-040 S1 draft and historical V2 extraction, replayed through the current candidate. Not a fresh V3 run or an EXP-044 result.'}),
        ('extraction_failure', 'Extraction failure · saved M3 round', failed, failed['calls']['S1']['output'],
         failed['calls']['V3']['output'],
         {'source':FAILURE, 'run_id':'0084deabb5bb478488123c78f5af864b', 'mode':'saved_demo_replay',
          'description':'Actual M3 local round, replayed without new inference. The extraction failure is not symbolic refutation.'}),
    ):
        trace = verify_saved_extraction(record['question'], record['documents'], draft, raw)
        if key=='extraction_failure' and trace!=failed['systems'][2]['trace']:
            raise ValueError('Saved M3 trace differs from replay')
        proof_view(record['question'],record['documents'],draft,raw,trace)
        examples.append({'example_id':key,'label':label,'question':record['question'],
                         'documents':record['documents'],'draft':draft,'raw_extraction':raw,
                         'trace':trace,'provenance':provenance,'source_sha256':PINNED[provenance['source']],
                         'new_model_calls':0})
    return examples
