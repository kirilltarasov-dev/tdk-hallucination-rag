"""UI-to-inference subprocess boundary; no model imports in the UI environment."""
import copy
import json
import os
from pathlib import Path
import subprocess
import uuid

from experiments.exp040_generated_answers import score
from src.arena.live import input_hash, verify_round

ROOT = Path(__file__).resolve().parents[2]


def run_local(question, documents):
    input_hash(question, documents)
    python = ROOT / '.venv/bin/python'
    if not python.exists():
        raise RuntimeError('The research .venv Python is unavailable; follow the local inference setup.')
    request = {'question': question, 'documents': documents, 'run_id': uuid.uuid4().hex}
    environment = {**os.environ, 'HF_HUB_OFFLINE': '1', 'HF_HUB_DISABLE_TELEMETRY': '1'}
    try:
        process = subprocess.run([str(python), '-B', '-u', '-m', 'src.arena.worker'],
                                 input=json.dumps(request, ensure_ascii=False), text=True,
                                 capture_output=True, cwd=ROOT, env=environment, timeout=180)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f'Local run timed out. Any partial logs remain in results/arena_runs/{request["run_id"]}.') from exc
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'Worker returned no valid result; inspect results/arena_runs/{request["run_id"]}.') from exc
    if process.returncode or 'error' in payload:
        raise RuntimeError(payload.get('error', 'Local generation failed'))
    if payload['run_id'] != request['run_id']:
        raise ValueError('Worker returned a different run ID')
    verify_round(payload['result'], question, documents)
    return payload


def decorate_live_case(challenge, payload):
    """Add fictional-reference scores after generation; never pass the oracle to a worker."""
    result = verify_round(payload['result'], challenge['question'], challenge['documents'])
    view = {key: copy.deepcopy(challenge[key]) for key in
            ('case_id', 'question', 'documents', 'family', 'family_label', 'authored_reference')}
    view['systems'] = copy.deepcopy(result['systems'])
    for system in view['systems']:
        system['score'] = score(system['answer'], challenge['authored_reference'])
    view.update(raw_record=result, live_payload=payload)
    return view


def export_live_case(case):
    return json.dumps({'artifact_type': 'arena_live_case_export', 'mode': 'live_local',
                       'case_id': case['case_id'], 'authored_reference': case['authored_reference'],
                       'reference_usage': 'Post-generation exact scoring only',
                       'systems_with_exact_scores': case['systems'],
                       **case['live_payload']}, indent=2, ensure_ascii=False)
