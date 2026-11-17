"""Authored finite-grammar controls, not independent semantic annotation."""
import json
from pathlib import Path

DATA=Path('data/synthetic/exp043_independent_claim_controls.json')


def build_cases():
    q='Who won the 2091 Opal Cup?'
    rows=[
        ('short','Saffron Larks won.','SINGLE_CLAIM','Saffron Larks'),
        ('year_first','Saffron Larks won the 2091 Opal Cup.','SINGLE_CLAIM','Saffron Larks'),
        ('year_last','Saffron Larks won the Opal Cup in 2091.','SINGLE_CLAIM','Saffron Larks'),
        ('repeated_same','Saffron Larks won. Saffron Larks won.','SINGLE_CLAIM','Saffron Larks'),
        ('rejected_quote','The claim "Cobalt Pumas won." is false. Saffron Larks won.','SINGLE_CLAIM','Saffron Larks'),
        ('contrast','Saffron Larks won, not Cobalt Pumas.','SINGLE_CLAIM','Saffron Larks'),
        ('other_claim','Cobalt Pumas won.','SINGLE_CLAIM','Cobalt Pumas'),
        ('refusal_one','I cannot determine the winner.','ABSTENTION',None),
        ('refusal_two','I do not know who won.','ABSTENTION',None),
        ('refusal_three','There is insufficient information to answer.','ABSTENTION',None),
        ('refusal_four','Insufficient information.','ABSTENTION',None),
        ('two_winners','Saffron Larks won. Cobalt Pumas won.','UNRESOLVED',None),
        ('self_negation','Saffron Larks won. Saffron Larks did not win.','UNRESOLVED',None),
        ('mixed_refusal','I cannot determine the winner. Saffron Larks won.','UNRESOLVED',None),
        ('negative_only','Cobalt Pumas did not win.','UNRESOLVED',None),
        ('quote_only','The claim "Cobalt Pumas won." is false.','UNRESOLVED',None),
        ('wrong_year','Saffron Larks won the 2090 Opal Cup.','UNRESOLVED',None),
        ('wrong_event','Saffron Larks won the 2091 Quartz Cup.','UNRESOLVED',None),
        ('answer_paraphrase','Saffron Larks took first place.','UNRESOLVED',None),
        ('auxiliary_claim','Saffron Larks won. The venue was large.','UNRESOLVED',None),
        ('bare_name','Saffron Larks','UNRESOLVED',None),
        ('hedged','Saffron Larks probably won.','UNRESOLVED',None),
        ('empty','','UNRESOLVED',None),
        ('refusal_and_denial','Cobalt Pumas did not win. I cannot determine the winner.','UNRESOLVED',None),
    ]
    return [{'case_id':f'C043-{i:02d}','condition':condition,'question':q,'response':response,
             'expected_status':status,'expected_value':value} for i,(condition,response,status,value) in enumerate(rows)]


if __name__=='__main__':
    with DATA.open('x') as handle:
        json.dump({'experiment_id':'EXP-043','provenance':'Authored development grammar controls',
                   'cases':build_cases()},handle,indent=2);handle.write('\n')
