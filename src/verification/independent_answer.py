"""Context-free claim parsing for the existing finite answer grammar.

Neural question/fact extraction is preserved. Replacing the neural answer field
is an explicit new component, not a repair of historical experimental records.
"""
from dataclasses import asdict
import re
import time

from src.verification.answer_claim_guard import inventory_answer, apply_answer_claim_guard
from src.verification.neuro_symbolic import Extraction, ExtractionError, parse_extraction
from src.verification.polarity_guard import apply_polarity_guard
from src.verification.prompt_polarity import build_prompt_v3
from src.verification.relation_guard import _name_supported, question_relation_supported
from src.verification.release_policy import ABSTENTION
from src.verification.symbolic_rules import AnswerClaim, QuestionFrame, RuleResult

VERSION = 'independent_finite_answer_v1'


def canonical(value):
    return ' '.join(value.casefold().split()) if isinstance(value,str) else value


def question_frame(question):
    """Read only supported question forms; never consult an extracted fact."""
    name = r"[A-Za-z0-9]+(?:[ '\-][A-Za-z0-9]+)*?"
    subject = r'(?:Who|Which team|Which player|Which competitor)'
    patterns = [
        rf'{subject}\s+won\s+(?:the\s+)?(?P<year>[1-9][0-9]{{3}})\s+(?P<event>{name})\??',
        rf'{subject}\s+won\s+(?:the\s+)?(?P<event>{name})\s+in\s+(?P<year>[1-9][0-9]{{3}})\??',
        rf'Who was the winner of\s+(?:the\s+)?(?P<year>[1-9][0-9]{{3}})\s+(?P<event>{name})\??',
    ]
    for pattern in patterns:
        match = re.fullmatch(pattern,question.strip(),re.IGNORECASE)
        if match and _name_supported(match['event']):
            frame=QuestionFrame('won',match['event'],int(match['year']))
            if question_relation_supported(question,frame):
                return frame
    return None


def read_answer(question, response):
    """The API has no document, evidence, neural-extraction or oracle argument."""
    frame=question_frame(question)
    inventory=inventory_answer(response,frame) if frame is not None else None
    status,value,reason='UNRESOLVED',None,'QUESTION_OUT_OF_SCOPE'
    if inventory is not None:
        positive={canonical(v) for v in inventory['asserted_values']}
        negative={canonical(v) for v in inventory['rejected_values']}
        if inventory['status']!='COMPLETE':reason='UNCONSUMED_RESPONSE_TEXT'
        elif len(positive)>1:reason='INCOMPATIBLE_ASSERTIONS'
        elif positive & negative:reason='ASSERTION_AND_NEGATION'
        elif positive and inventory['abstention_detected']:reason='MIXED_ASSERTION_AND_ABSTENTION'
        elif len(positive)==1:
            status,value,reason='SINGLE_CLAIM',inventory['asserted_values'][0],'COMPLETE_SINGLE_ASSERTION'
        elif inventory['abstention_detected'] and not negative:
            status,reason='ABSTENTION','COMPLETE_ABSTENTION'
        else:reason='NO_SUPPORTED_POSITIVE_CLAIM'
    return {'component_version':VERSION,'status':status,'value':value,'source_span':response,
            'reason':reason,'question_frame':asdict(frame) if frame is not None else None,
            'inventory':inventory,'uses_source_documents':False}


def verify_saved_extraction(question, documents, response, raw):
    """Compose a new claim with unchanged, strictly validated question/facts."""
    independent=read_answer(question,response)
    trace={'component_version':VERSION,'independent_answer':independent,
           'original_neural_answer':None,'original_unresolved':None,
           'replacement_applied':False,'validation_error':None,
           'preserved_question':None,'preserved_facts':None,
           'source_trace':None,'answer_trace':None,'factual_truth_verified':False}

    def unknown(rule,reason):
        return {**trace,'decision':RuleResult('UNKNOWN',rule,reason,()).trace()}

    try:
        original=parse_extraction(raw,question,documents,response)
    except ExtractionError as exc:
        trace['validation_error']=str(exc)
        return unknown('I1_ORIGINAL_EXTRACTION_INVALID',str(exc))
    trace.update(original_neural_answer=asdict(original.answer),
                 original_unresolved=list(original.unresolved),
                 preserved_question=asdict(original.question) if original.question else None,
                 preserved_facts=[asdict(f) for f in original.facts])
    if independent['status']=='UNRESOLVED':
        return unknown('I2_INDEPENDENT_ANSWER_UNRESOLVED',independent['reason'])
    if original.question is None or any(x!='answer:UNRESOLVED' for x in original.unresolved):
        return unknown('I3_NONANSWER_UNRESOLVED','Question or source extraction remains unresolved.')
    frame=QuestionFrame(**independent['question_frame'])
    if any(canonical(getattr(frame,k))!=canonical(getattr(original.question,k))
           for k in ('relation','event','year','subject')):
        return unknown('I4_QUESTION_FRAME_MISMATCH','Text-only and neural question frames disagree.')
    claim=AnswerClaim(independent['value'],independent['status']=='ABSTENTION')
    composed=Extraction(original.question,original.facts,claim,())
    source=apply_polarity_guard(question,documents,composed)
    answer=apply_answer_claim_guard(response,composed,source['decision'])
    trace.update(replacement_applied=True,source_trace=source,answer_trace=answer,
                 composed_answer=asdict(claim),decision=answer['decision'])
    return trace


def verify_and_release(question, documents, response, generate):
    """Live candidate adapter; joint V3 facts call is unchanged and fully logged.

    The joint prompt still generates an unused neural answer field. Only the
    independently parsed claim is used for the new decision, if validation passes.
    """
    prompt=build_prompt_v3(question,documents,response)
    start=time.perf_counter()
    raw=generate(user_prompt=prompt,max_tokens=1024)
    seconds=time.perf_counter()-start
    result=verify_saved_extraction(question,documents,response,raw)
    release=result['decision']['verdict']=='VERIFIED'
    return {'prompt':prompt,'raw_extraction':raw,'extraction_latency_seconds':seconds,
            'verification':result,'action':'RELEASE' if release else 'ABSTAIN',
            'final_answer':response if release else ABSTENTION,
            'factual_truth_verified':False}
