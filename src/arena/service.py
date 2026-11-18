"""Admitted local inference and explicit, integrity-checked archive import."""
import argparse
import copy
import json
import sqlite3

from src.arena.attacks import verify_insertion
from src.arena.client import run_local
from src.arena.replay import load_challenges
from src.arena.scoreboard import Ledger, ROOT
from src.arena.worker import verify_saved_run


def canonical_case(case,attack=None):
    base=next((c for c in load_challenges() if c['case_id']==case['case_id']),None)
    if base is None or case['question']!=base['question'] or case['authored_reference']!=base['authored_reference']:
        raise ValueError('Challenge metadata differs from the canonical fixture')
    if attack:
        if list(attack['base_documents'].items())!=list(base['documents'].items()):
            raise ValueError('Attack has a different base context')
        verify_insertion(attack,case['question'],case['documents'])
    elif list(case['documents'].items())!=list(base['documents'].items()):
        raise ValueError('Changed sources require attack provenance')
    return base


def run_tracked(case,participant,*,attacker=False,attack=None,ledger=None,runner=None):
    canonical_case(case,attack)
    if attacker and attack is not None:
        raise ValueError('AI proposals must start from the canonical base context')
    try:
        ledger=ledger or Ledger()
        run_id=ledger.begin(participant,'proposal' if attacker else 'evaluation')
    except sqlite3.Error as exc:
        raise RuntimeError('Ledger unavailable; inference was not started.') from exc
    try:
        payload=(runner or run_local)(case['question'],case['documents'],attacker=attacker,attack=attack,run_id=run_id)
        ledger.finish(run_id,case,payload)
        return payload
    except Exception as exc:
        try:
            ledger.fail(run_id,exc)
        except sqlite3.Error:
            pass  # Raw logs remain recoverable even during a ledger outage.
        raise RuntimeError(f'Request {run_id} failed: {exc}. Completed raw calls, if any, remain in their run directory.') from exc


def import_archives(ledger):
    base=next(c for c in load_challenges() if c['case_id']=='E044-005')
    imported=[]
    for milestone,run_id in [('m2','b01d842a926048d5a2c6fe7b6e622fa6'),
                              ('m3','25dce8eb7c874d6aa5c11064dde62c07'),
                              ('m3','0084deabb5bb478488123c78f5af864b')]:
        directory=ROOT/f'results/demo/arena_{milestone}_smoke'/run_id
        result=verify_saved_run(directory)
        payload={'run_id':run_id,'result':result,'saved_directory':str(directory.relative_to(ROOT))}
        case=copy.deepcopy(base)
        case['documents']=result['documents']
        attack_path=directory/'attack.json'
        if attack_path.exists():payload['attack']=json.loads(attack_path.read_text())
        canonical_case(case,payload.get('attack'))
        added=ledger.finish(run_id,case,payload,archive=True)
        imported.append({'run_id':run_id,'added':added})
    return imported


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--import-archives',action='store_true',required=True)
    parser.add_argument('--database')
    args=parser.parse_args()
    print(json.dumps(import_archives(Ledger(args.database)),indent=2))
