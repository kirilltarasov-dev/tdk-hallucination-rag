"""Build a separate manuscript from v8 and the completed frozen EXP-046.

Use the bundled document Python runtime. Render and inspect the output, then
apply --pages with a verified heading/page map and render again. Historical
manuscripts, experiment code and raw outcomes are never modified.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from report_exp046 import load_completed

SOURCE = Path('deliverables/TDK_Research_Paper_v8_Kirill_Tarasov.docx')
SOURCE_HASH = '1c090c2300e79f9f7c6ad4d6f36c6b063a84b023983ad621ba621d384aa268b5'
ARMS = ('S1', 'S2', 'Candidate_NS')
ARM_LABELS = ('Standard RAG', 'Same-model review', 'Candidate hybrid')
FAMILIES = ('clean', 'paraphrase', 'negated_distractor', 'conflict', 'no_target_evidence', 'false_source_only')


def interval(values):
    return f'[{values[0]:+.3f}, {values[1]:+.3f}]'


def build(output):
    if output.exists():
        raise FileExistsError(output)
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_HASH:
        raise ValueError('The v8 reference changed')
    result, cases, rows = load_completed()
    doc = Document(SOURCE)
    original = list(doc.paragraphs)
    s1, s2, ns = [result['metrics'][a]['counts'] for a in ARMS]
    retained, denominator = result['retained_correct'], result['S1_correct_denominator']
    retain_text = f'{retained}/{denominator} ({retained/denominator:.1%})' if denominator else 'undefined'
    bounds = interval(result['primary_paired_utility_bounds'])
    envelope = interval(result['stratified_bootstrap_95pct_sensitivity_envelope'])
    outcome = {'NOT_PASS': 'did not pass', 'INCONCLUSIVE': 'was inconclusive',
               'PASS_RESTRICTED_ENGINEERING_SCREEN': 'passed within the restricted fixture'}[result['screen']]
    endpoint = (f'The 240-question study {outcome} under the predeclared joint criterion. '
                f'The candidate-minus-standard-RAG utility bounds were {bounds}, '
                f'with a conditional bootstrap envelope of {envelope}; '
                f'correct-draft retention was {retain_text}.')

    def before(anchor, text='', style=None):
        p = doc.add_paragraph(text, style)
        anchor._p.addprevious(p._p)
        return p

    def caption(anchor, text):
        p = before(anchor, text)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(7)
        p.paragraph_format.space_after = Pt(4)
        for r in p.runs:
            r.bold = True
        return p

    def figure(anchor, path, text):
        p = before(anchor)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(path), width=Cm(15.7))
        c = before(anchor, text)
        c.paragraph_format.line_spacing = 1.1
        c.paragraph_format.space_after = Pt(8)
        for r in c.runs:
            r.font.size = Pt(10)

    def table(anchor, data, widths):
        t = doc.add_table(rows=0, cols=len(widths))
        t.autofit = False
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for column, width in zip(t.columns, widths):
            column.width = Cm(width)
        for values in data:
            for cell, value in zip(t.add_row().cells, values): cell.text = str(value)
        anchor._p.addprevious(t._tbl)
        # Copy the checked table design; set each new column deliberately.
        props = t._tbl.tblPr
        borders = OxmlElement('w:tblBorders')
        for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            e = OxmlElement('w:' + side)
            for k, v in [('val', 'single'), ('sz', '4'), ('color', 'D9D9D9')]: e.set(qn('w:'+k), v)
            borders.append(e)
        props.append(borders)
        for ri, row in enumerate(t.rows):
            trpr = row._tr.get_or_add_trPr()
            trpr.append(OxmlElement('w:cantSplit'))
            if ri == 0: trpr.append(OxmlElement('w:tblHeader'))
            for ci, (cell, width) in enumerate(zip(row.cells, widths)):
                cell.width = Cm(width)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                pr = cell._tc.get_or_add_tcPr()
                shade = OxmlElement('w:shd');shade.set(qn('w:fill'), 'E7E6E6' if ri == 0 else 'FFFFFF');pr.append(shade)
                margins = OxmlElement('w:tcMar')
                for side in ('top', 'left', 'bottom', 'right'):
                    m = OxmlElement('w:'+side);m.set(qn('w:w'), '75');m.set(qn('w:type'), 'dxa');margins.append(m)
                pr.append(margins)
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT if ci == 0 else WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.line_spacing = 1.05
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(3)
                    p.paragraph_format.keep_with_next = ri == 0
                    for r in p.runs:
                        r.font.name = 'Times New Roman';r.font.size = Pt(10);r.bold = ri == 0
                        r.font.color.rgb = RGBColor(0, 0, 0)
        return t

    original[54].text = (
        'This study evaluates evidence filtering and restricted neuro-symbolic verification with a fixed 4-bit Mistral-7B model. '
        'On 300 RGB questions at 80% noise, hard filtering reduced the lexical score from 268 to 251 correct answers; an empty-context fallback raised it to 276. '
        'Its advantage over standard RAG was not established and did not transfer to 60% noise. '
        'A 40-question fictional pilot removed seven scored errors but withheld eight correct answers, failing its utility and retention criterion. '
        'Diagnosing source-conditioned answer transcription led to a candidate that retained six additional correct drafts over the original hybrid in a 24-question transfer study. '
        f'A subsequent frozen five-passage evaluation on 240 new authored questions produced {s1["CORRECT"]} correct and {s1["WRONG"]} wrong standard-RAG answers, '
        f'compared with {ns["CORRECT"]} correct and {ns["WRONG"]} wrong candidate answers; '
        f'{s1["UNSCORABLE"]} standard-RAG responses were outside the scoring contract. '
        + endpoint + ' The contribution is a reproducible diagnosis of evidence and verification failures, a restricted hybrid and a local demonstrator. '
        'The results do not establish general hallucination reduction or source credibility.')

    # Verified external literature; numbered temporary keys are reordered below.
    before(original[74], 'Lewis et al. introduced a retrieval-augmented architecture that combines a parametric sequence generator with a non-parametric Wikipedia index accessed by a neural retriever [5]. This distinction matters for the present study: supplied evidence lets us isolate downstream generation and verification, but it does not evaluate index construction, retrieval recall or the original jointly trained RAG architecture.')
    before(original[76], 'Answer correctness, source support and factual truth are different evaluation targets. FActScore decomposes generated text into atomic claims and measures the fraction supported by a reliable knowledge source [9]. Its human evaluation and automated estimator are separate from the whole-answer lexical scores used here. The fictional experiments have authored reference winners, but their automatic output-contract utility is neither FActScore nor an independently validated semantic hallucination rate.')
    before(original[76], 'Liu et al. show that relevant-information position can substantially affect performance in multi-document question answering and key-value retrieval, with information in the middle of long contexts often harder to use [6]. This motivates explicit control of passage order. The five-source study balances a designated passage across positions, while keeping that positional control distinct from a replication of long-context behavior.')
    before(original[81], '2.4 Neural extraction and symbolic reasoning', 'Heading 2')
    before(original[81], 'LINC separates semantic parsing from deductive inference: a language model translates natural-language premises and conclusions into first-order logic, and an external theorem prover determines entailment [7]. Faithful Chain-of-Thought similarly separates model-produced representations from deterministic execution [8]. These approaches make a concrete distinction between generating a plausible explanation and executing explicit reasoning over a representation.')
    before(original[81], 'The present candidate uses typed event-winner facts and explicit Python rules instead of a general first-order prover. It does not reproduce LINC or Faithful Chain-of-Thought. Its scope permits direct checks of source polarity, event/year agreement, competing winners and complete answer consumption. A correct rule result is conditional on its accepted inputs: erroneous translation, unsupported language and false sources remain separate failure modes. The independent answer parser specifically addresses contamination of answer transcription by the evidence context; it does not establish the truth of that evidence.')

    figure(original[103], Path('results/figures/candidate_verifier_architecture.png'),
           'Figure 1. Implemented candidate verification branch. Neural extraction sees the draft and sources; the independent claim parser sees only the question and draft. Full source text is checked again during validation and polarity/coverage analysis. Invalid intermediate outputs lead to UNKNOWN. Same-model review is a separate comparison arm. Authored truth enters scoring only; no source-credibility oracle is implemented.')
    before(original[103], '3.8 Frozen evaluation with five supplied passages', 'Heading 2')
    before(original[103], 'A fixed evaluation uses 240 new fictional questions, forty in each of six families: clean evidence, paraphrase, a negated distractor, conflicting target statements, no target evidence and a consistently false target source. Each question has exactly five ordered passages and a unique authored target winner. The first three families provide 120 unambiguous true-evidence cases; all forty false-source controls remain in the primary denominator. These are new identities constructed from familiar mechanism templates, not an independent sample of scientific literature.')
    before(original[103], 'Standard RAG generates one draft. Matched same-model review and the unchanged candidate both receive that draft and the same ordered sources; their call order alternates. The pinned 4-bit Mistral revision and greedy decoding are fixed, with 128-token draft/review caps and a 1,024-token extraction cap. Configuration, fixture, prompts, rules and analysis were frozen in a tagged commit before inference. There is no retrieval, repair, retry or selective router in this evaluation.')
    before(original[103], 'The frozen full-response contract assigns +1 to CORRECT, -1 to WRONG and 0 to the canonical ABSTAIN. UNSCORABLE responses retain unknown utility in [-1, +1]. For each question, the candidate-minus-draft utility is bounded; identical released strings cancel exactly even if unscorable. The primary interval averages all 240 lower and upper endpoints. The positive criterion requires a lower endpoint above zero, a positive lower endpoint under 10,000 within-family bootstrap resamples, and at least 80% retention of contract-correct drafts. The bootstrap envelope describes sensitivity within the fixed authored mixture, not population uncertainty. The retention Wilson interval is descriptive; its lower endpoint is not the acceptance threshold.')

    before(original[158], '5.12 Frozen evaluation on 240 questions', 'Heading 2')
    before(original[158], 'All 240 questions and 720 model calls completed using the frozen method. The same process survived a laptop sleep interval; there was no runner restart or case replacement. The complete saved calls, decisions, scores and aggregate analysis were replayed before interpretation. ' + endpoint)
    caption(original[158], 'Table 9. Frozen output-contract outcomes on 240 questions.')
    data = [['Outcome', *ARM_LABELS]]
    for key, label in [('CORRECT', 'Correct'), ('WRONG', 'Wrong'), ('ABSTAIN', 'Abstain'), ('UNSCORABLE', 'Unscorable')]:
        data.append([label, *[result['metrics'][a]['counts'][key] for a in ARMS]])
    data.append(['Mean utility bounds', *[interval(result['metrics'][a]['mean_utility_bounds']) for a in ARMS]])
    table(original[158], data, [4.6, 3.8, 3.8, 3.8])
    caption(original[158], 'Table 10. Per-family correct / wrong / abstain / unscorable counts; n = 40 per row.')
    data = [['Evidence family', 'Standard RAG', 'Same-model review', 'Candidate hybrid']]
    for family in FAMILIES:
        data.append([family.replace('_', ' ').capitalize(), *[
            ' / '.join(str(result['by_family'][family][a]['counts'][k]) for k in ('CORRECT', 'WRONG', 'ABSTAIN', 'UNSCORABLE')) for a in ARMS]])
    table(original[158], data, [4.6, 3.8, 3.8, 3.8])
    figure(original[158], Path('results/figures/exp046_primary_bounds.png'),
           'Figure 2. Paired utility bounds and correct-draft retention. The bootstrap envelope resamples paired questions within the six fixed families and preserves unresolved utility. It is conditional sensitivity for this authored mixture. The 80% criterion applies to point retention, not the lower Wilson endpoint.')
    before(original[158],
           f'The candidate released {result["candidate_false_source_releases"]}/40 false-source controls. '
           f'It produced {result["candidate_extraction_validation_failures"]} original-extraction validation failures and '
           f'{result["at_token_cap_by_stage"]["V3"]} extraction outputs at the 1,024-token cap. '
           f'On the 120 unambiguous true-evidence cases it abstained {result["metrics"]["Candidate_NS"]["false_abstentions"]} times. '
           'These diagnostics distinguish loss of answer coverage from source credibility: a valid extraction and a VERIFIED decision can still describe a consistently false source. Reduced wrong-answer counts alone do not establish benefit because this policy only releases or withholds an unchanged draft.')
    before(original[158], 'The candidate returned UNKNOWN on all 236 withheld cases; no final REFUTED or CONFLICT verdict was produced. Of the 76 correct drafts lost, 45 stopped at source-coverage validation and 31 at original-extraction validation. This identifies a coverage collapse: the zero scored WRONG count is accompanied by only one retained contract-correct answer. All forty conflicting-source questions also stopped as UNKNOWN, so their refusals cannot be counted as successful conflict detection.')
    before(original[158], 'A post-run diagnostic audit, restricted to the 176 extractions that passed original schema/provenance validation, found missing facts for 482/683 affirmative non-target statements and 14/175 affirmative target statements. At least one non-target positive fact was absent in 170/176 valid cases. The prompt explicitly requires preserving facts with a different event or year, but the model often filtered them out. No extraction reached the token cap. These diagnostics do not isolate passage count as a causal factor, because evidence composition and fictional identities also differ from the smaller transfer study.')
    before(original[158], 'The sole released false-source control asserted “Fawn Condors won the 2203 Acacia Grove Cup.” Its source names that competitor, but the authored reference is Pistachio Ferrets. The response remains UNSCORABLE under the frozen “TEAM won.” contract; it is not relabelled as WRONG in the primary analysis. This example shows why zero scored wrong answers does not establish zero false assertions or source credibility.')
    secondary = result['secondary_descriptive_paired_bounds']
    before(original[158], f'The secondary same-model-review-minus-standard-RAG utility bounds were {interval(secondary["S2_minus_S1"])}; candidate-minus-review bounds were {interval(secondary["Candidate_NS_minus_S2"])}. These descriptive comparisons do not replace the single predeclared primary criterion. No independent human semantic labels or hallucination-rate significance test were obtained.')
    before(original[158],
           f'The recorded workload was {result["unique_model_calls"]} calls, {result["unique_input_tokens"]:,} input tokens and '
           f'{result["unique_output_tokens"]:,} generated tokens. Peak MLX process allocation was {result["peak_MLX_process_memory_GB"]:.3f} GB. '
           'The S1 call is shared, so summing arm totals would double-count it. Laptop sleep and concurrent document/desktop work make timings execution telemetry rather than an isolated benchmark; original timings and outliers are preserved. No computational-efficiency improvement is claimed.')

    original[166].text = ('The experiments show that additional validation can remove useful evidence or withhold correct answers. A fallback repaired 25 hard-filter development outcomes, but broader benefit was not established and did not transfer. Independent answer parsing was part of a candidate that recovered six correct drafts over the original hybrid on 24 authored questions. The subsequent five-passage evaluation exposed a severe coverage failure: only 1/77 correct drafts was retained, far below the 80% requirement. Missing source facts and invalid extractions accounted for all 76 lost correct drafts. The paired utility bounds [-0.592, +0.325] also do not establish a positive effect. These reproducible failures identify limits of the implemented pipeline; general hallucination reduction, source credibility and effectiveness on natural scientific literature remain unestablished.')
    discussion = next(p for p in original if p.text.startswith('The hybrid is implemented with explicit Python rules'))
    discussion.text = discussion.text.replace('All consistently false-source controls still pass.', 'Consistently false sources can pass when extraction validates. Zero scored wrong answers in the larger study accompanies near-total abstention and an unscorable false-source release, rather than established source credibility.')
    before(original[162], 'The full-source guard itself recognizes the authored sentence grammar. A rule-only baseline was not included in the five-passage experiment, so the results cannot establish that neural extraction is necessary or superior to direct parsing in this domain. Fresh names across six fixed mechanism templates also provide limited diversity. Testing component necessity, natural-text coverage and genuinely new evidence mechanisms requires a separate prospective design.')
    original[169].text = 'RQ3 — Partially answered: safe fallback repaired a specific development failure without establishing broader benefit. The revised hybrid improved coverage over its predecessor on 24 authored questions, but failed the larger five-passage retention criterion. Neither a reliable advantage over standard RAG nor independently validated hallucination reduction has been demonstrated.'
    original[172].text = 'The fixed 240-question study is complete. The next controlled development step should distinguish complete transcription from relevance filtering and include a rule-only comparator for this finite grammar. Further prompt changes require a new protocol and genuinely new evaluation data. Source credibility, natural scientific text and actual retrieval remain broader research priorities. Increasing the authored sample after observing the result would not resolve the identified coverage failure or these scope limitations.'
    original[180].text = 'Experiment identifiers are retained here for reproducibility. Development, frozen transfer, offline analysis and software acceptance are separate evidence levels. The five-passage evaluation is complete. The repository retains original raw results, frozen manifests and experiment-specific reports; later analyses do not replace earlier primary outcomes.'
    original[185].text = 'Fictional fixtures and their hashes are preserved under data/synthetic and the experiment-specific manifests. Their authored reference winners define controlled worlds, not real events. The five-passage fixture contains 240 completed cases.'
    contributions = [
        'I implemented the experimental comparisons of generation, same-model review and evidence filtering.',
        'I diagnosed empty-context failures and tested safe fallback, preserving negative transfer results.',
        'I developed the restricted hybrid and fictional tests, investigated extraction failures, froze prospective methods and analysed outcomes with explicit uncertainty bounds.',
        'I implemented the Arena with source traces and separate records for real calls and simulations.',
    ]
    for number, contribution in enumerate(contributions, 1):
        p = before(original[187], f'{number}. '+contribution)
        p.paragraph_format.left_indent = Cm(.5)
        p.paragraph_format.first_line_indent = Cm(-.5)
        p.paragraph_format.space_after = Pt(4)
    original[187].text = 'Róbert Lakatos supervised the research and reviewed the manuscript. RGB, Mistral and dependencies are external inputs. Retrospective assistant labels lack independent human validation.'
    original[174].paragraph_format.page_break_before = True
    for t in doc.tables:
        if t.rows[0].cells[0].text == 'Identifier':
            for row in t.rows:
                if row.cells[0].text == 'EXP-046':
                    row.cells[1].text = f'Frozen 240-question five-passage evaluation; 720 calls; {result["screen"]}'
                    for p in row.cells[1].paragraphs:
                        p.paragraph_format.line_spacing = 1.05
                        for r in p.runs: r.font.size = Pt(9.5)

    references = {str(i): original[174+i].text.split('] ', 1)[1] for i in range(1, 5)}
    references.update({
        '5': 'P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W.-t. Yih, T. Rocktäschel, S. Riedel, and D. Kiela, “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” Advances in Neural Information Processing Systems, vol. 33, pp. 9459–9474, 2020.',
        '6': 'N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, and P. Liang, “Lost in the Middle: How Language Models Use Long Contexts,” Transactions of the Association for Computational Linguistics, vol. 12, pp. 157–173, 2024. doi: 10.1162/tacl_a_00638.',
        '7': 'T. X. Olausson, A. Gu, B. Lipkin, C. E. Zhang, A. Solar-Lezama, J. B. Tenenbaum, and R. Levy, “LINC: A Neurosymbolic Approach for Logical Reasoning by Combining Language Models with First-Order Logic Provers,” Proceedings of EMNLP, pp. 5153–5176, 2023. doi: 10.18653/v1/2023.emnlp-main.313.',
        '8': 'Q. Lyu, S. Havaldar, A. Stein, L. Zhang, D. Rao, E. Wong, M. Apidianaki, and C. Callison-Burch, “Faithful Chain-of-Thought Reasoning,” Proceedings of IJCNLP-AACL, vol. 1, pp. 305–329, 2023. doi: 10.18653/v1/2023.ijcnlp-main.20.',
        '9': 'S. Min, K. Krishna, X. Lyu, M. Lewis, W.-t. Yih, P. W. Koh, M. Iyyer, L. Zettlemoyer, and H. Hajishirzi, “FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation,” Proceedings of EMNLP, pp. 12076–12100, 2023. doi: 10.18653/v1/2023.emnlp-main.741.',
    })
    order = {}
    for p in doc.paragraphs:
        if p._p is original[174]._p: break
        for match in re.finditer(r'\[(\d+)\]', p.text):
            key = match[1]
            if key not in references: raise ValueError(f'Unknown citation {key}')
            order.setdefault(key, len(order)+1)
        if re.search(r'\[\d+\]', p.text):
            p.text = re.sub(r'\[(\d+)\]', lambda m: '['+str(order[m[1]])+']', p.text)
    if set(order) != set(references): raise ValueError('Every reference must be cited')
    for p in original[175:179]: p._p.getparent().remove(p._p)
    for key, number in order.items():
        p = before(original[179], f'[{number}] '+references[key])
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(8)
        for r in p.runs: r.font.size = Pt(10.5)

    # Rebuild the static contents after all heading insertions.
    for p in original[12:53]: p._p.getparent().remove(p._p)
    headings = [p for p in doc.paragraphs if p.style.name in ('Heading 1', 'Heading 2') and p.text != 'Contents']
    for h in headings:
        p = before(original[53], h.text+'\t0')
        p.paragraph_format.line_spacing = 1
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.left_indent = Cm(.35 if h.style.name == 'Heading 2' else 0)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(15.7), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        for r in p.runs: r.font.size = Pt(9.5);r.bold = h.style.name == 'Heading 1'
    doc.core_properties.subject = 'TDK research manuscript with completed five-passage evaluation'
    doc.save(output)


def update_pages(output, mapping):
    doc = Document(output)
    pages = json.loads(Path(mapping).read_text())
    active = False
    for p in doc.paragraphs:
        if p.text == 'Contents': active = True
        elif p.text == 'Abstract' and p.style.name == 'Heading 1': break
        elif active:
            text = p.text.rsplit('\t', 1)[0]
            if text not in pages: raise ValueError(f'Missing heading: {text}')
            p.runs[0].text = text+'\t'+str(pages[text])
    doc.save(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('deliverables/TDK_Research_Paper_v9_Kirill_Tarasov.docx'))
    parser.add_argument('--pages')
    args = parser.parse_args()
    if args.pages: update_pages(args.output, args.pages)
    else: build(args.output)
    print(args.output)
