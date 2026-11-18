"""Reproducible software-only accounting and admission evidence; no model calls."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from threading import Barrier
import tempfile
import uuid

from src.arena.scoreboard import Ledger, AdmissionDenied
from tests.test_arena_ledger import hundred_round_check


def main():
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        simulation=hundred_round_check(root/'counts.sqlite3')
        ledger=Ledger(root/'admission.sqlite3')
        barrier=Barrier(20)
        def enter(index):
            local=Ledger(ledger.path);barrier.wait(timeout=20)
            try:
                local.begin(f'{index:032x}','evaluation',kind='software_simulation',now=1000)
                return 'accepted'
            except AdmissionDenied:return 'denied'
        with ThreadPoolExecutor(max_workers=20) as pool:outcomes=list(pool.map(enter,range(20)))
        assert outcomes.count('accepted')==1 and outcomes.count('denied')==19
        sources=['src/arena/scoreboard.py','src/arena/service.py','tests/test_arena_ledger.py',__file__]
        report={'artifact_type':'arena_m5_software_acceptance','created_utc':datetime.now(timezone.utc).isoformat(),
                'status':'passed','model_calls':0,'simulation':simulation,
                'admission':{'simultaneous_clients':20,'accepted':outcomes.count('accepted'),
                             'denied':outcomes.count('denied')},
                'source_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
                'scope':'Temporary-database software fixtures only; not measured answers or inference throughput.'}
    target=Path('results/demo/arena_m5_acceptance')/uuid.uuid4().hex
    target.mkdir(parents=True)
    with (target/'report.json').open('x') as handle:json.dump(report,handle,indent=2);handle.write('\n')
    print(json.dumps({'status':'passed','report':str(target/'report.json'),'model_calls':0}))


if __name__=='__main__':main()
