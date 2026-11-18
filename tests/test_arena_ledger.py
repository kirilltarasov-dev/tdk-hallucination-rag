"""M5 accounting/admission tests; all generated call strings are software fixtures."""
import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
from threading import Barrier
import unittest
import uuid

from src.arena.attacks import insert_passage
from src.arena.live import run_round
from src.arena.replay import load_challenges
from src.arena.scoreboard import AdmissionDenied, Ledger, summarize
from src.arena.service import canonical_case, import_archives, run_tracked


def simulated_round(index,base):
    case=copy.deepcopy(base)
    attack=None
    if index%2:
        case['documents'],attack=insert_passage(base['question'],base['documents'],
            'Obsidian Otters won the 2135 Willow Cup.',0,'Entity swap')
    answers=('Crimson Swans won.','Obsidian Otters won.','I cannot determine the winner.',
             'A speculative answer outside the required format.')
    draft=answers[index%4]
    extraction={'schema_version':'event_winner_v1',
        'question':{'status':'IN_SCOPE','event':'Willow Cup','year':2135,'source_span':case['question']},
        'documents':[{'source_id':sid,'status':'COMPLETE','facts':[
            {'source_span':text,'event':'Willow Cup','year':2135,
             'value':'Obsidian Otters' if sid=='A1' else 'Crimson Swans'}]} for sid,text in case['documents'].items()],
        'answer':{'status':('SINGLE_CLAIM','SINGLE_CLAIM','ABSTENTION','UNRESOLVED')[index%4],
                  'value':('Crimson Swans','Obsidian Otters',None,None)[index%4],'source_span':draft}}
    def generate(stage,prompt,cap):
        output={'S1':draft,'S2':answers[(index+1)%4],'V3':json.dumps(extraction)}[stage]
        return {'stage':stage,'prompt':prompt,'max_tokens':cap,'output':output,
                'chat_prompt':'SOFTWARE SIMULATION, NOT A MODEL CALL','latency_seconds':0,
                'input_tokens':0,'output_tokens':0}
    result=run_round(case['question'],case['documents'],generate)
    payload={'run_id':uuid.uuid4().hex,'result':result,'saved_directory':'SOFTWARE_SIMULATION_ONLY'}
    if attack:payload['attack']=attack
    return case,payload


def reserve_fixture(ledger,payload,index):
    # Storage stress is separate from admission: no worker is invoked or bypassed.
    with ledger.connection(write=True) as db:
        db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?)',
            (payload['run_id'],f'{index:032x}','evaluation','software_simulation','RUNNING',1000+index,99999,None))


def hundred_round_check(path):
    ledger=Ledger(path)
    base=load_challenges()[4]
    fixtures=[simulated_round(i,base) for i in range(100)]
    for i,(_,payload) in enumerate(fixtures):reserve_fixture(ledger,payload,i)
    barrier=Barrier(20)
    def client(worker):
        own=Ledger(path)
        barrier.wait(timeout=20)
        for index in range(worker,100,20):
            case,payload=fixtures[index]
            assert own.finish(payload['run_id'],case,payload)
            assert not own.finish(payload['run_id'],case,payload)
    with ThreadPoolExecutor(max_workers=20) as pool:list(pool.map(client,range(20)))
    records=ledger.records('software_simulation')
    assert len(records)==100 and len({r['run_id'] for r in records})==100
    table=summarize(records)
    expected={
        ('No insertion','S1'):(25,0,25,0), ('No insertion','S2'):(0,25,0,25),
        ('No insertion','Candidate_NS'):(25,0,25,0),
        ('Entity swap','S1'):(0,25,0,25), ('Entity swap','S2'):(25,0,25,0),
        ('Entity swap','Candidate_NS'):(0,0,50,0)}
    for row in table:
        assert tuple(row[k] for k in ('CORRECT','WRONG','ABSTAIN','UNSCORABLE'))==expected[(row['Attack origin'],row['System'])]
        assert row['Rounds']==50
    assert len(ledger.export_jsonl('software_simulation').splitlines())==100
    assert ledger.records('live_demo')==[] and ledger.records('archived_demo')==[]
    return {'artifact_type':'arena_m5_software_simulation_check','model_calls':0,
            'simulated_rounds':100,'concurrent_database_clients':20,'outcomes':300,
            'duplicate_writes_ignored':100,'counts':table,
            'scope':'Explicit software fixtures; not attack efficacy or concurrent model-serving throughput.'}


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'ledger.sqlite3'
        self.ledger=Ledger(self.path)
        self.base=load_challenges()[4]

    def tearDown(self):self.temp.cleanup()

    def test_100_rounds_20_database_clients_counts_and_idempotence(self):
        self.assertEqual(hundred_round_check(self.path)['outcomes'],300)

    def test_20_simultaneous_admission_attempts_accept_exactly_one(self):
        barrier=Barrier(20)
        def attempt(i):
            ledger=Ledger(self.path);barrier.wait(timeout=20)
            try:return ledger.begin(f'{i:032x}','evaluation',kind='software_simulation',now=1000)
            except AdmissionDenied:return None
        with ThreadPoolExecutor(max_workers=20) as pool:ids=list(pool.map(attempt,range(20)))
        self.assertEqual(sum(x is not None for x in ids),1)
        states=[a['state'] for a in self.ledger.attempts('software_simulation')]
        self.assertEqual(states.count('DENIED'),19)
        self.assertEqual(states.count('RUNNING'),1)

    def test_session_global_limits_and_expired_leases(self):
        participant='a'*32
        for i in range(6):
            rid=self.ledger.begin(participant,'proposal',now=1000+i)
            self.ledger.fail(rid,'SIMULATED FAILURE')
        with self.assertRaisesRegex(AdmissionDenied,'Session limit'):
            self.ledger.begin(participant,'evaluation',now=1007)
        rid=self.ledger.begin(participant,'evaluation',now=1606)
        new=self.ledger.begin('b'*32,'proposal',now=1847)
        self.assertEqual(next(a for a in self.ledger.attempts('live_demo') if a['id']==rid)['state'],'INTERRUPTED')
        self.ledger.fail(new,'SIMULATED FAILURE')
        # Global quota uses new participants, so resetting a session does not bypass it.
        accepted=len([a for a in self.ledger.attempts('live_demo') if a['state']!='DENIED'])
        for i in range(30-accepted):
            rid=self.ledger.begin(f'{i:032x}','proposal',now=1900)
            self.ledger.fail(rid,'SIMULATED FAILURE')
        with self.assertRaisesRegex(AdmissionDenied,'Global limit'):
            self.ledger.begin('c'*32,'evaluation',now=1901)
        self.assertEqual(self.ledger.records('live_demo'),[])

    def test_different_duplicate_payload_and_database_tamper_rejected(self):
        case,payload=simulated_round(0,self.base);reserve_fixture(self.ledger,payload,0)
        self.ledger.finish(payload['run_id'],case,payload)
        altered={**payload,'saved_directory':'DIFFERENT'}
        with self.assertRaisesRegex(ValueError,'different content'):
            self.ledger.finish(payload['run_id'],case,altered)
        with self.ledger.connection(write=True) as db:
            db.execute("UPDATE rounds SET payload='{}'")
        with self.assertRaisesRegex(ValueError,'integrity mismatch'):
            self.ledger.records('software_simulation')

    def test_service_passes_no_reference_and_failure_is_not_wrong_answer(self):
        captured=[]
        def fail(question,documents,**kwargs):
            captured.append((question,documents,kwargs));raise RuntimeError('SIMULATED WORKER FAILURE')
        with self.assertRaisesRegex(RuntimeError,'SIMULATED WORKER FAILURE'):
            run_tracked(self.base,'a'*32,ledger=self.ledger,runner=fail)
        self.assertEqual(set(captured[0][2]),{'attacker','attack','run_id'})
        self.assertEqual(self.ledger.attempts('live_demo')[0]['state'],'FAILED')
        self.assertEqual(summarize(self.ledger.records('live_demo')),[])

    def test_canonical_reference_and_attack_base_cannot_be_changed(self):
        for field,value in [('authored_reference','Different winner'),('documents',{'D1':'Changed.'})]:
            with self.assertRaises(ValueError):canonical_case({**self.base,field:value})

    def test_archives_import_once_and_keep_proposals_out_of_score_counts(self):
        self.assertTrue(all(x['added'] for x in import_archives(self.ledger)))
        self.assertTrue(all(not x['added'] for x in import_archives(self.ledger)))
        rows=self.ledger.records('archived_demo')
        self.assertEqual(len(rows),3)
        self.assertEqual(sum(row['Rounds'] for row in summarize(rows)),6)
        self.assertEqual(self.ledger.records('live_demo'),[])
        exported=[json.loads(line) for line in self.ledger.export_jsonl('archived_demo').splitlines()]
        self.assertTrue(all(r['origin']=='archived_demo' and r['round'] for r in exported))

    def test_service_completion_binds_admission_and_post_generation_scores(self):
        _, fixture=simulated_round(0,self.base)
        def runner(question,documents,**kwargs):
            self.assertEqual(question,self.base['question'])
            self.assertEqual(documents,self.base['documents'])
            self.assertEqual(set(kwargs),{'attacker','attack','run_id'})
            return {**fixture,'run_id':kwargs['run_id']}
        result=run_tracked(self.base,'a'*32,ledger=self.ledger,runner=runner)
        stored=self.ledger.records('live_demo')[0]
        self.assertEqual(stored['run_id'],result['run_id'])
        self.assertEqual(stored['exact_scores']['S1']['category'],'CORRECT')
        self.assertEqual(self.ledger.attempts('live_demo')[0]['state'],'COMPLETED')

    def test_entry_URL_validation(self):
        from src.arena.entry import validate_url
        for url in ('http://127.0.0.1:8501','https://example.org/arena?event=tdk'):
            self.assertEqual(validate_url(url),url)
        for url in ('javascript:alert(1)','https://user:secret@example.org',None,'http://host:bad','https://x/with space'):
            with self.assertRaises(ValueError):validate_url(url)

    def test_ledger_failure_blocks_worker_before_inference(self):
        import sqlite3
        from unittest.mock import Mock
        broken=Mock()
        broken.begin.side_effect=sqlite3.OperationalError('SIMULATED database outage')
        runner=Mock()
        with self.assertRaisesRegex(RuntimeError,'inference was not started'):
            run_tracked(self.base,'a'*32,ledger=broken,runner=runner)
        runner.assert_not_called()
