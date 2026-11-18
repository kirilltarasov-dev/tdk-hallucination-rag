"""UI-to-inference subprocess boundary; no model imports in the UI environment."""
import copy
import json
import os
from pathlib import Path
import subprocess
import uuid

from experiments.exp040_generated_answers import score
from src.arena.attacks import verify_attacker, verify_insertion
from src.arena.worker import save_new, sha, validate_request
from src.arena.live import input_hash, verify_round

ROOT = Path(__file__).resolve().parents[2]


def run_local(question, documents, *, attacker=False, attack=None, run_id=None):
    if attack is not None:
        verify_insertion(attack, question, documents)
    input_hash(question, documents)
    python = ROOT / '.venv/bin/python'
    if not python.exists():
        raise RuntimeError('The research .venv Python is unavailable; follow the local inference setup.')
    request = {'question': question, 'documents': documents, 'run_id': run_id or uuid.uuid4().hex}
    validate_request(request)
    environment = {**os.environ, 'HF_HUB_OFFLINE': '1', 'HF_HUB_DISABLE_TELEMETRY': '1'}
    try:
        command = [str(python), '-B', '-u', '-m', 'src.arena.worker']
        if attacker:
            command.append('--attacker')
        process = subprocess.run(command,
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
    verifier = verify_attacker if attacker else verify_round
    verifier(payload['result'], question, documents)
    if attack is not None:
        directory = ROOT / 'results/arena_runs' / request['run_id']
        save_attack_provenance(directory, attack, question, documents)
        payload['attack'] = attack
    return payload


def save_attack_provenance(directory, attack, question, documents):
    verify_insertion(attack, question, documents)
    path = Path(directory) / 'attack.json'
    save_new(path, attack)
    save_new(Path(directory) / 'attack_integrity.json', {'sha256': sha(path),
              'result_sha256': sha(Path(directory) / 'result.json')})


def decorate_live_case(challenge, payload):
    """Add fictional-reference scores after generation; never pass the oracle to a worker."""
    if 'attack' in payload:
        verify_insertion(payload['attack'], challenge['question'], challenge['documents'])
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
