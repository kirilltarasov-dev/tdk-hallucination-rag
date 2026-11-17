"""Development prompt variant; unchanged positive-fact schema and strict parser."""
import json

from src.verification.prompt_clarity import INSTRUCTION_V2

PROMPT_VERSION = 'event_winner_polarity_examples_v3'
ADDITION = '''
ADDITIONAL EXTRACTION CONVENTIONS
"took first place in" is an affirmative win paraphrase. Preserve that exact
document quotation and copy its event, year and winner as a positive fact.
"did not win" and "did not take first place in" are NEGATIVE statements.
The positive-fact schema cannot encode those statements. For a document with
only such a negative statement, write status COMPLETE and facts: [].
NEVER create a fact whose event, year or value is null. Do not convert a negative
statement to an affirmative one. Read every document independently. A negative
statement about one competitor does not erase another document's positive win.
Keep positive statements even when a separate source denies them: the symbolic
source audit, not this transcription, will check positive/negative conflict.
Reported, hypothetical or quoted-and-denied wins are not positive assertions.

Document examples (different fictional entities, no verdicts):
Input {"source_id":"N1","text":"Bronze Kites did not win the 2059 Meridian Shield."}
Output {"source_id":"N1","status":"COMPLETE","facts":[]}
Input {"source_id":"N2","text":"Bronze Kites did not take first place in the 2059 Meridian Shield."}
Output {"source_id":"N2","status":"COMPLETE","facts":[]}
Input {"source_id":"P1","text":"Coral Badgers took first place in the 2059 Meridian Shield."}
Output {"source_id":"P1","status":"COMPLETE","facts":[{"source_span":"Coral Badgers took first place in the 2059 Meridian Shield.","event":"Meridian Shield","year":2059,"value":"Coral Badgers"}]}
'''


def build_prompt_v3(question, documents, answer):
    return INSTRUCTION_V2 + ADDITION + '\nINPUT DATA:\n' + json.dumps({
        'question':question,'documents':[{'source_id':k,'text':v} for k,v in documents.items()],
        'response':answer},ensure_ascii=False)
