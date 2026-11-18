"""SQLite demo ledger; score accounting is separate from inference and efficacy."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import uuid

from experiments.exp040_generated_answers import score
from src.arena.attacks import verify_attacker, verify_insertion
from src.arena.live import verify_round

ROOT = Path(__file__).resolve().parents[2]
KINDS = ('live_demo', 'archived_demo', 'software_simulation')
CATEGORIES = ('CORRECT','WRONG','ABSTAIN','UNSCORABLE')


def encoded(value):
    # Preserve document insertion order, including in the integrity digest.
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def default_path():
    return Path(os.environ.get('TDK_ARENA_DB', ROOT/'results/arena_state/arena.sqlite3'))


class AdmissionDenied(RuntimeError):
    pass


class Ledger:
    def __init__(self, path=None):
        self.path=Path(path) if path is not None else default_path()
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connection() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS attempts (
                  id TEXT PRIMARY KEY, participant TEXT NOT NULL, task TEXT NOT NULL,
                  kind TEXT NOT NULL, state TEXT NOT NULL, created REAL NOT NULL,
                  lease_until REAL NOT NULL, error TEXT);
                CREATE TABLE IF NOT EXISTS rounds (
                  id TEXT PRIMARY KEY REFERENCES attempts(id), kind TEXT NOT NULL,
                  task TEXT NOT NULL, attack_type TEXT NOT NULL, created REAL NOT NULL,
                  payload TEXT NOT NULL, sha256 TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS attempt_time ON attempts(created);
            ''')

    @contextmanager
    def connection(self, write=False):
        db=sqlite3.connect(self.path,timeout=10,isolation_level=None)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            if write: db.execute('BEGIN IMMEDIATE')
            yield db
            if write: db.commit()
        except BaseException:
            if write: db.rollback()
            raise
        finally: db.close()

    def begin(self, participant, task, *, kind='live_demo', now=None):
        if not isinstance(participant,str) or not re.fullmatch('[a-f0-9]{32}',participant):
            raise ValueError('Participant must be an anonymous session ID')
        if task not in ('evaluation','proposal') or kind not in ('live_demo','software_simulation'):
            raise ValueError('Invalid admission task or origin')
        now=time.time() if now is None else now
        run_id=uuid.uuid4().hex
        error=None
        with self.connection(write=True) as db:
            db.execute("UPDATE attempts SET state='INTERRUPTED', error='Admission lease expired' WHERE state='RUNNING' AND lease_until<=?",(now,))
            active=db.execute("SELECT count(*) FROM attempts WHERE state='RUNNING'").fetchone()[0]
            recent=db.execute("SELECT count(*) FROM attempts WHERE participant=? AND kind=? AND state!='DENIED' AND created>?",(participant,kind,now-600)).fetchone()[0]
            global_count=db.execute("SELECT count(*) FROM attempts WHERE kind=? AND state!='DENIED' AND created>?",(kind,now-3600)).fetchone()[0]
            if active: error='Another request is running. Wait for it to finish.'
            elif recent>=6: error='Session limit: six requests per ten minutes.'
            elif global_count>=30: error='Global limit: thirty requests per hour.'
            db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?)',
                       (run_id,participant,task,kind,'DENIED' if error else 'RUNNING',now,now+240,error))
        if error: raise AdmissionDenied(error)
        return run_id

    def fail(self,run_id,error):
        with self.connection(write=True) as db:
            db.execute("UPDATE attempts SET state='FAILED', error=? WHERE id=? AND state='RUNNING'",(str(error)[:1000],run_id))

    def finish(self,run_id,case,payload,*,archive=False):
        if payload.get('run_id')!=run_id or not re.fullmatch('[a-f0-9]{32}',run_id):
            raise ValueError('Payload run ID mismatch')
        result=payload['result']
        proposal=result.get('mode')=='attack_proposal'
        task='proposal' if proposal else 'evaluation'
        if proposal:
            verify_attacker(result,case['question'],case['documents'])
            scores={}
        else:
            verify_round(result,case['question'],case['documents'])
            scores={s['system_id']:score(s['answer'],case['authored_reference']) for s in result['systems']}
        attack=payload.get('attack')
        if attack:
            verify_insertion(attack,case['question'],case['documents'])
        record={'artifact_type':'arena_ledger_round','run_id':run_id,'task':task,
                'case_id':case['case_id'],'question':case['question'],'documents':case['documents'],
                'authored_reference':case['authored_reference'],'reference_usage':'Post-generation scoring only',
                'attack_type':attack['origin'] if attack else 'No insertion','exact_scores':scores,
                'payload':payload,'scope':'Demonstration accounting; not an independent efficacy sample.'}
        with self.connection(write=True) as db:
            attempt=db.execute('SELECT * FROM attempts WHERE id=?',(run_id,)).fetchone()
            if archive and attempt is None:
                db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?)',
                           (run_id,'archived',task,'archived_demo','IMPORTED',time.time(),0,None))
                attempt=db.execute('SELECT * FROM attempts WHERE id=?',(run_id,)).fetchone()
            if attempt is None or attempt['task']!=task:
                raise ValueError('Round has no matching admission')
            if archive and attempt['kind']!='archived_demo':
                raise ValueError('Cannot relabel a live request as archived')
            record.update(origin=attempt['kind'],participant=attempt['participant'],created=attempt['created'])
            fingerprint=digest(record)
            existing=db.execute('SELECT sha256 FROM rounds WHERE id=?',(run_id,)).fetchone()
            if existing:
                if existing['sha256']!=fingerprint: raise ValueError('Run ID already contains different content')
                return False
            if attempt['state'] not in ('RUNNING','IMPORTED'):
                raise ValueError('Admission is no longer active; raw run remains available')
            db.execute('INSERT INTO rounds VALUES (?,?,?,?,?,?,?)',
                       (run_id,attempt['kind'],task,record['attack_type'],attempt['created'],encoded(record),fingerprint))
            db.execute("UPDATE attempts SET state='COMPLETED' WHERE id=?",(run_id,))
        return True

    def records(self,kind):
        if kind not in KINDS: raise ValueError('Invalid record origin')
        with self.connection() as db:
            rows=db.execute('SELECT payload,sha256 FROM rounds WHERE kind=? ORDER BY created,id',(kind,)).fetchall()
        records=[]
        for row in rows:
            value=json.loads(row['payload'])
            if digest(value)!=row['sha256']: raise ValueError('Ledger record integrity mismatch')
            records.append(value)
        return records

    def attempts(self,kind):
        if kind not in KINDS: raise ValueError('Invalid attempt origin')
        with self.connection() as db:
            return [dict(row) for row in db.execute('SELECT * FROM attempts WHERE kind=? ORDER BY created,id',(kind,))]

    def export_jsonl(self,kind):
        if kind not in KINDS: raise ValueError('Invalid record origin')
        # One SELECT gives attempts and results from the same SQLite snapshot.
        with self.connection() as db:
            rows=db.execute('SELECT a.*,r.payload,r.sha256 FROM attempts a LEFT JOIN rounds r ON a.id=r.id '
                            'WHERE a.kind=? ORDER BY a.created,a.id',(kind,)).fetchall()
        output=[]
        for row in rows:
            attempt=dict(row)
            raw=attempt.pop('payload');fingerprint=attempt.pop('sha256')
            record=json.loads(raw) if raw is not None else None
            if record is not None and digest(record)!=fingerprint:
                raise ValueError('Ledger record integrity mismatch')
            output.append(encoded({'artifact_type':'arena_ledger_export','origin':kind,
                                   'attempt':attempt,'round':record})+'\n')
        return ''.join(output)


def summarize(records):
    groups={}
    for record in records:
        if record['task']!='evaluation': continue
        for system,score_result in record['exact_scores'].items():
            key=(record['origin'],record['attack_type'],system)
            row=groups.setdefault(key,{'Origin':key[0],'Attack origin':key[1],'System':system,'Rounds':0,
                                      **{c:0 for c in CATEGORIES}})
            category=score_result['category']
            if category not in CATEGORIES: raise ValueError('Unknown exact-score category')
            row['Rounds']+=1
            row[category]+=1
    return [groups[key] for key in sorted(groups)]
