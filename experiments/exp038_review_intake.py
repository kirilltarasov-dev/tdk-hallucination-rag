"""Validate an actual author review of EXP-038 assistant drafts without unblinding."""
import argparse
import json
from datetime import datetime,timezone
from pathlib import Path
from experiments.exp037_assisted_annotation import DATA,sha256
from experiments.exp037_review_intake import validate_export
from experiments.exp038_author_drafts import TABLE,OUTPUT as PROPOSALS


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export',type=Path)
    parser.add_argument('--lock',type=Path)
    args=parser.parse_args()
    proposals=json.loads(PROPOSALS.read_text())
    if proposals['source_sha256']!=sha256(DATA) or proposals['authored_table_sha256']!=sha256(TABLE):
        raise ValueError('Source/draft provenance differs')
    data=json.loads(args.export.read_text())
    report=validate_export(data,proposals['records'],sha256(DATA),sha256(TABLE),sha256(PROPOSALS),experiment_id='EXP-038')
    print(json.dumps(report,indent=2))
    if args.lock:
        if report['status']!='COMPLETE_ASSISTED_AUTHOR_REVIEW':
            raise ValueError('Only an actual complete valid author export can be locked')
        with args.lock.open('x',encoding='utf-8') as handle:
            json.dump({'experiment_id':'EXP-038','artifact_type':'locked_assisted_author_review',
                       'locked_at_utc':datetime.now(timezone.utc).isoformat(),'export_sha256':sha256(args.export),
                       'validation':report,'original_export':data},handle,indent=2,ensure_ascii=False)
            handle.write('\n')
    if report['status']=='INVALID':
        raise SystemExit(2)


if __name__=='__main__':
    main()
