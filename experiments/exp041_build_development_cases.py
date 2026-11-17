"""Hand-authored mechanism fixtures, explicitly development data."""
import json
from pathlib import Path

DATA=Path('data/synthetic/exp041_polarity_development.json')


def build_cases():
    rows=[]
    conditions=[
        ('clean','VERIFIED'), ('paraphrase','VERIFIED'), ('wrong_year','UNKNOWN'),
        ('negative_distractor','VERIFIED'), ('negative_first','VERIFIED'),
        ('positive_negative_conflict','CONFLICT'), ('negative_only','UNKNOWN'),
        ('negative_paraphrase','UNKNOWN'), ('reported_paraphrase','UNKNOWN'),
        ('hypothetical_paraphrase','UNKNOWN'), ('not_only_phrase','UNKNOWN'),
        ('denied_quote','UNKNOWN'), ('false_source','VERIFIED'),
        ('two_positive_conflict','CONFLICT'), ('wrong_answer','REFUTED'),
        ('false_abstention','REFUTED')]
    events=['Cedar Shield','Maple Trophy','Birch Cup','Elm Medal','Laurel Prize',
            'Willow Shield','Cypress Trophy','Alder Cup','Hazel Medal','Aspen Prize',
            'Rowan Shield','Spruce Trophy','Larch Cup','Beech Medal','Oak Prize','Fir Shield']
    for i,(family,expected) in enumerate(conditions):
        event,year=events[i],2061+i
        winner,other='Amber Cranes','Indigo Lynxes'
        positive=f'{winner} won the {year} {event}.'
        negative=f'{other} did not win the {year} {event}.'
        # Each tuple declares affirmative facts independently of the parser.
        sources={
            'clean':[(positive,winner,year)],
            'paraphrase':[(f'{winner} took first place in the {year} {event}.',winner,year)],
            'wrong_year':[(f'{winner} took first place in the {year-1} {event}.',winner,year-1)],
            'negative_distractor':[(positive,winner,year),(negative,None,year)],
            'negative_first':[(negative,None,year),(positive,winner,year)],
            'positive_negative_conflict':[(positive,winner,year),(f'{winner} did not win the {year} {event}.',None,year)],
            'negative_only':[(f'{winner} did not win the {year} {event}.',None,year)],
            'negative_paraphrase':[(f'{winner} did not take first place in the {year} {event}.',None,year)],
            'reported_paraphrase':[(f'A report claimed {winner} took first place in the {year} {event}.',None,year)],
            'hypothetical_paraphrase':[(f'If {winner} took first place in the {year} {event}, they would celebrate.',None,year)],
            'not_only_phrase':[(f'{winner} not only won the {year} {event}, they set a record.',winner,year)],
            'denied_quote':[(f'The claim "{winner} took first place in the {year} {event}." is false.',None,year)],
            'false_source':[(f'{other} won the {year} {event}.',other,year)],
            'two_positive_conflict':[(positive,winner,year),(f'{other} won the {year} {event}.',other,year)],
            'wrong_answer':[(positive,winner,year)], 'false_abstention':[(positive,winner,year)]
        }[family]
        question=f'Who won the {year} {event}?'
        response=(other if family in ('false_source','wrong_answer') else winner)+' won.'
        if family=='false_abstention': response='I cannot determine the winner.'
        documents={f'D{j+1}':s[0] for j,s in enumerate(sources)}
        oracle={'schema_version':'event_winner_v1',
                'question':{'status':'IN_SCOPE','event':event,'year':year,'source_span':question},
                'documents':[{'source_id':f'D{j+1}','status':'COMPLETE',
                              'facts':[] if value is None else [{'source_span':text,'event':event,'year':y,'value':value}]}
                             for j,(text,value,y) in enumerate(sources)],
                'answer':{'status':'ABSTENTION' if family=='false_abstention' else 'SINGLE_CLAIM',
                          'value':None if family=='false_abstention' else response[:-5],
                          'source_span':response}}
        rows.append({'case_id':f'D041-{i:02d}','family':family,'question':question,
                     'documents':documents,'response':response,'oracle_extraction':oracle,
                     'expected_source_verdict':expected,
                     'external_fictional_truth':winner if family=='false_source' else None})
    return rows


if __name__=='__main__':
    with DATA.open('x') as handle:
        json.dump({'experiment_id':'EXP-041','status':'authored_development_fixtures',
                   'cases':build_cases()},handle,indent=2);handle.write('\n')
