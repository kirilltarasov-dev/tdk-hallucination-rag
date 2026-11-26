"""Export exact prompt builders without loading a model or changing experiments."""
import ast
import __future__
import hashlib
import json
from pathlib import Path
import sys
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def isolated(path, symbol, extra=None):
    tree = ast.parse(Path(path).read_text())
    node = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == symbol)
    env = {'dataclass': dataclass, 'MistralModel': object, **(extra or {})}
    exec(compile(ast.Module(body=[node], type_ignores=[]), path, 'exec', flags=__future__.annotations.compiler_flag), env)
    return env[symbol]


def catalog():
    from src.evaluation.rgb_prompt import RGB_SYSTEM_PROMPT, build_rgb_user_prompt
    from src.verification.neuro_symbolic import EXTRACTION_INSTRUCTION, build_extraction_prompt
    from src.verification.prompt_clarity import INSTRUCTION_V2, build_prompt_v2
    from src.verification.prompt_polarity import ADDITION, build_prompt_v3
    from experiments.exp040_generated_answers import prompt
    from src.arena.attacks import attacker_prompt
    q, d, a = '{question}', '{document}', '{draft_answer}'
    entries = []

    def add(key, title, source, text, note):
        entries.append({'id': key, 'title': title, 'source': source, 'text': text,
                        'sha256': hashlib.sha256(text.encode()).hexdigest(), 'note': note})

    p = 'experiments/exp010_s0_full_baseline.py'
    add('s0', 'Question only generation', p, isolated(p, 'build_prompt')(q), 'S0 baseline; 256 output tokens.')
    add('rgb', 'RGB generation and filtered regeneration', 'src/evaluation/rgb_prompt.py',
        RGB_SYSTEM_PROMPT+'\n\n'+build_rgb_user_prompt(q, ['{newline_joined_documents}']),
        'S1 and S3 generation share this template. Insert the selected ordered passages joined by one newline. System and user strings are joined by two newlines in one user message; 256 output tokens.')
    for key, title, p, cls, args, note in [
        ('review', 'Historical RGB answer verification', 'src/verification/universal_verifier.py', 'UniversalVerifier', (q, '{evidence}', a), 'S2 historical verifier; 256 output tokens. Evidence is the ordered document text.'),
        ('support', 'Four class evidence support', 'src/diagnosis/evidence_support_assessor.py', 'EvidenceSupportAssessor', (q,d), 'S3 support assessor; one passage per call, 64 output tokens.'),
        ('diagnosis', 'Evidence condition development probe', 'src/diagnosis/failure_diagnoser.py', 'FailureDiagnoser', (q,'{evidence}'), 'Historical holistic development probe; 128 output tokens.'),
        ('relevance', 'Binary relevance development probe', 'src/diagnosis/relevance_detector.py', 'RelevanceDetector', (q,d), 'Historical binary development probe; 64 output tokens.'),
    ]:
        add(key,title,p,isolated(p,cls)._build_prompt(*args),note)

    class Capture:
        def generate(self, **kwargs):
            self.text=kwargs['system_prompt']+'\n\n'+kwargs['user_prompt']
            return 'DECISION: SKIP\nTYPE: NONE\nREASON: documentation capture'

    for key,title,p,cls,method in [
        ('router','Verification routing','src/verification/verification_router.py','VerificationRouter','route'),
        ('claim_router','Claim type routing prototype','src/verification/claim_router.py','ClaimRouter','classify'),
    ]:
        capture=Capture()
        c=isolated(p,cls)
        c._parse=staticmethod(lambda x:x)
        getattr(c(capture),method)(q,[d],a)
        add(key,title,p,capture.text,'96 output tokens. Repeat numbered [Document i] blocks, joined by two newlines, in source order. The claim-type prototype is not a measured selective S4 system.' if key=='claim_router' else '96 output tokens. Repeat numbered [Document i] blocks, joined by two newlines, in source order. One user message combines both instruction strings.')

    case={'question':q,'documents':{'{source_id}':d}}
    for key,title,draft in [('fiction_s1','Fictional answer generation',None),('fiction_s2','Fictional same model review',a)]:
        add(key,title,'experiments/exp040_generated_answers.py',prompt(case,draft),
            'Shared fictional protocol used in the generated-answer studies; 128 output tokens. JSON document keys preserve input order. Braced values denote substitutions, not model instructions.')
    add('v1','Original extraction instruction','src/verification/neuro_symbolic.py',EXTRACTION_INSTRUCTION,
        'V1 instruction, followed by the shared extraction input suffix; 1,024 output tokens.')
    add('v2','Revised extraction instruction','src/verification/prompt_clarity.py',INSTRUCTION_V2,
        'V2 instruction, followed by the shared extraction input suffix; 1,024 output tokens. V3 reuses this entire instruction unchanged.')
    add('v3_addition','Additional polarity conventions','src/verification/prompt_polarity.py',ADDITION,
        'V3 concatenates the entire V2 instruction, this addition and the shared extraction input suffix, without trimming any component; 1,024 output tokens.')
    suffix=build_extraction_prompt(q,{'{source_id}':d},a)[len(EXTRACTION_INSTRUCTION):]
    assert build_prompt_v2(q,{'{source_id}':d},a)==INSTRUCTION_V2+suffix
    assert build_prompt_v3(q,{'{source_id}':d},a)==INSTRUCTION_V2+ADDITION+suffix
    add('extraction_input','Shared extraction input suffix','src/verification/neuro_symbolic.py',suffix,
        'Replace placeholder values and serialize with json.dumps(..., ensure_ascii=False), preserving ordered source IDs. Reference truth and scenario labels are absent.')
    # Use a valid finite-domain question for the demo input validator, then replace
    # only that placeholder value. This does not execute an attacker or generator.
    demo_q='Who won the 2099 Documentation Cup?'
    attack=attacker_prompt(demo_q,{'D1':d}).replace(demo_q,q).replace('"D1"','"{source_id}"')
    add('attacker','Arena attack proposal','src/arena/attacks.py',attack,
        'Demo-only optional attacker; 256 output tokens. Proposal text is not a validated attack success result.')
    p='experiments/exp002_s1_clean.py'
    add('early_rag','Early RAG smoke template',p,isolated(p,'build_rag_prompt')(q,[d]),
        'Early smoke template, superseded by the RGB template in reported full runs. Number document blocks in input order.')
    assert isolated('experiments/exp001_s0.py','build_prompt')(q)==entries[0]['text']
    assert isolated('experiments/exp003_s1_noise.py','build_rag_prompt')(q,[d])==entries[-1]['text']
    p='experiments/exp037_assisted_annotation.py'
    tree=ast.parse(Path(p).read_text())
    instruction=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INSTRUCTION' for t in n.targets))
    docs=isolated(p,'documents',{'re':__import__('re')})
    annotation=isolated(p,'build_prompt',{'INSTRUCTION':instruction,'json':json,'documents':docs})
    case={'question':q,'benchmark_reference_answer':'{benchmark_reference_answer}',
          **{k+'_'+arm:('D1: '+d if k=='context' else '{response_'+arm+'}') for arm in ('A','B') for k in ('context','response')}}
    add('annotation','Machine annotation draft labels',p,annotation(case),
        'Historical draft-label proposal only; 1,024 output tokens. Unlike answer generation and verification, this annotation input includes the provisional benchmark reference. It is not independent human validation.')
    sources=sorted({x['source'] for x in entries}|{'src/models/mistral.py','src/models/pinned_mistral.py'})
    return {'scope':'Exact local application prompt templates and shared components; not conversation history or a public release.',
            'wrapper':'Application strings enter a single user message via tokenizer.apply_chat_template(..., tokenize=False, add_generation_prompt=True). The pinned tokenizer supplies model control tokens.',
            'source_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},'entries':entries}


if __name__=='__main__':
    out=Path(sys.argv[1])
    data=catalog()
    with out.open('x') as f:json.dump(data,f,indent=2,ensure_ascii=False);f.write('\n')
    print(len(data['entries']), 'templates/components;',sum(len(x['text']) for x in data['entries']),'characters; no model calls')
