"""Build a separate supervisor manuscript with canonical results through EXP-045.

Run with the bundled document runtime. Optional --pages reads a JSON mapping
from headings to PDF page numbers after pagination; it changes only the TOC.
No experiment is executed or relabelled by this script.
"""

import argparse
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SOURCE = Path('deliverables/TDK_Research_Paper_v7_Kirill_Tarasov.docx')
OUTPUT = Path('deliverables/TDK_Research_Paper_v8_Kirill_Tarasov.docx')


def build():
    doc = Document(SOURCE)
    p = list(doc.paragraphs)

    replacements = {
        47: 'This study evaluates evidence filtering and a restricted neuro-symbolic release policy with a fixed 4-bit Mistral-7B model. On 300 RGB questions at 80% noise, hard filtering reduced the lexical score from 268 to 251 correct answers; an empty-context fallback raised it to 276. The fallback repaired 25 hard-filter outcomes without damage, but its advantage over standard RAG was not established and did not transfer to 60% noise. A subsequent 40-question fictional pilot removed seven scored errors while withholding eight correct answers, failing its utility and retention screen. After diagnosing context-dependent answer transcription, a frozen 24-question transfer study retained 12 correct answers instead of six under the original symbolic policy. Both policies still released four wrong answers supported by consistently false sources. The candidate retained 12/14 correct standard-RAG drafts, but its utility difference from standard RAG remained bounded by [−0.167, +0.167] because four drafts violated the scoring contract. The work provides reproducible failure diagnoses, a limited hybrid verifier and a local interactive demonstrator. It does not establish general hallucination reduction or source credibility.',
        51: 'This research examines how a fixed small language model responds to relevant and noisy external evidence. It measures standard RAG, same-model self-verification and document-level evidence filtering, then evaluates a restricted hybrid verifier that combines neural fact extraction with deterministic rules. The distinction between checking consistency with supplied sources and establishing factual truth is central to the study. Actual retrieval over scientific literature and a complete selective verification pipeline remain unevaluated.',
        52: 'The experiments establish a question-only baseline and a standard-RAG noise curve, diagnose failures at 80% noise and compare filtering policies on paired questions. Frozen tests examine lower noise and counterfactual sources. A separate fictional event-winner task then isolates extraction, answer transcription, polarity and source-conflict failures. Generated-answer pilots measure the cost of withholding correct answers alongside the removal of wrong answers. An interactive RAG Red-Team Arena exposes these decisions and their limitations.',
        71: 'The experiments use one fixed small model and controlled evidence rather than reproducing the complete Self-RAG or CRAG architectures. This design isolates particular filtering and verification mechanisms. It cannot establish comparative performance against those published systems or against larger models.',
        73: 'Retrieval-side correction does not guarantee an evidence-supported answer. A model may ignore a relevant passage, confuse a date or entity, or make an unsupported inference. The first verification baseline uses a second pass of the generator model. The later restricted hybrid instead validates neural extractions and applies explicit deterministic rules, producing VERIFIED, REFUTED, CONFLICT or UNKNOWN. Its decision logic is symbolic, but its coverage depends on extraction and a finite supported language. Selective use of this hybrid has not been evaluated end to end.',
        76: 'The RGB systems comprise a question-only baseline (S0), standard RAG with supplied passages (S1), same-model self-verification (S2), and document-level filtering with hard rejection or safe fallback (S3). A VERIFY/SKIP router was evaluated on saved drafts, followed by an offline S4 policy simulation. Later experiments evaluate a separate restricted neuro-symbolic release policy on fictional event-winner tasks. This policy is not a completed selective S4 system, and its same-model review comparator uses a matched answer-format prompt rather than the historical RGB verdict parser.',
        79: p[79].text + ' Later generated-answer pilots use 128 output tokens for drafts and matched-format review, and up to 1,024 for structured extraction. The fresh 24-question study pins model revision a4b8f870474b0eb527f466a03fbc187830d271f5 and uses greedy decoding. Historical model-name records alone do not establish the exact revision loaded during earlier runs.',
        85: p[85].text + ' The fictional pilots use an exact complete-response contract: a named winner followed by “won.”, or the canonical abstention. CORRECT, WRONG and ABSTAIN receive utility +1, −1 and 0; other responses remain UNSCORABLE with utility bounded by [−1, +1]. This declared task utility is not a hallucination metric. Factual truth relative to the authored world, support by supplied sources, and completeness of an answer are distinct properties.',
        88: p[88].text + ' The later counterfactual study uses new RGB questions, and the fictional transfer uses prospectively fixed new identities. Neither substitutes for independent semantic evaluation on naturally occurring scientific text. The fictional worlds and mechanism templates are developer-authored. Independent human validation of the later semantic reviews has not been completed.',
        106: p[106].text + ' Subsequent hybrid-verifier studies address a restricted event-winner relation and do not resolve the selective-verification research question.',
        132: 'The filtering comparison isolates a concrete damaging branch: removing every passage forced abstention on questions that standard RAG could answer. Restoring the original context prevented 25 such damages without changing the nonempty filtering branch. The later verifier studies reveal a different failure: extraction may reinterpret a fixed answer in light of the sources. Separating answer transcription from evidence-dependent extraction restored a known refutation in offline development; a combined candidate subsequently retained six additional correct answers relative to the older verifier on fresh fictional cases. These are bounded mechanism findings, not evidence of a general benefit across tasks.',
        133: 'Several limitations affect interpretation. RGB passages were supplied rather than retrieved by an index. Lexical matching can misclassify semantic correctness, and assessor false negatives were observed. Assessment averaged 5.463 s per question in the original filtering run; the later 0.894 s fallback figure covers generation only because assessments were reused. Router latency averaged 2.073 s before verification, so fewer verifier calls do not establish computational savings. The historical verifier parser sometimes retained drafts after an INSUFFICIENT verdict. New-question counterfactual and fictional conflict tests now exist, but natural-text retrieval and independent human-validated error rates remain absent.',
        134: 'The hybrid is implemented with explicit Python rules; it does not use clingo or Z3 and is not a general theorem prover. Neural extraction, schema validation and deterministic inference are separate stages. The candidate changes both extraction instructions and the decision bundle, so its improvement over the original policy cannot be attributed to the independent answer component alone. All consistently false-source controls still pass. Same-model review is not an independent model judge, and retrospective assistant judgments are not independent human evidence. These boundaries constrain what can be concluded under the thesis title.',
        136: 'The work identifies and tests two classes of reliability failure. Aggressive evidence filtering can remove information required for correct answers; a targeted fallback repaired 25 development outcomes, but broader filtering benefit was not established. Restricted neural extraction can also distort an answer before symbolic reasoning begins. A revised hybrid retained six more correct drafts than its predecessor on 24 fresh fictional cases while leaving four false-source errors unchanged. Its comparison with standard RAG remains inconclusive under the frozen scoring contract. The negative 40-question pilot, extraction regressions and false-source failures remain part of the evidence. General hallucination reduction has not been demonstrated.',
        139: 'RQ3 — Partially answered: safe fallback repaired a specific hard-filter failure but did not establish an advantage over standard RAG. The revised hybrid improved correct-answer coverage over the original hybrid on the authored transfer fixture. Its standard-RAG comparison is inconclusive, and source-consistent factual errors remain.',
        142: 'The next proposed evaluation keeps the current method and exact scorer unchanged on a new 240-question fictional fixture with five passages per question. It compares standard RAG, matched-format same-model review and the candidate hybrid. The primary question is whether the hybrid has a positive paired output-contract utility difference while retaining at least 80% of contract-correct standard-RAG answers. Unscorable responses contribute explicit bounds rather than new retrospective labels. The design is specified but has no frozen execution manifest, completed fixture, runner or results. It is not a powered natural-language hallucination study.',
        143: 'External reviewers are unavailable for the planned study, so its conclusions must remain restricted to automatic contract scoring. Broad semantic validation, a distinct neural verifier, actual scientific-literature retrieval and source-credibility handling remain separate work. The Arena requires a final five-passage demonstration collection, venue and phone-access checks, audience evaluation and a video. The literature review and public reproducibility package also need completion before submission. These tasks must not be represented as completed by local software tests.',
        150: 'Experiment identifiers are retained here for reproducibility. Development, frozen transfer, offline analysis and software acceptance are separate evidence levels. The proposed next evaluation has not run. The repository retains original raw results, frozen manifests and experiment-specific reports; later analyses do not replace earlier primary outcomes.',
        153: 'I developed the project-specific experiment scripts and controlled comparisons in the accompanying research repository. I implemented and evaluated the no-retrieval, standard-RAG, self-verification and evidence-filtering variants; investigated high-noise failures; identified the empty-context failure; and tested safe fallback and its transfer. I developed the restricted neural-extraction and deterministic-verification pipeline, investigated answer-transcription failures, and evaluated generated-answer release policies on authored fictional cases. I also implemented the local Arena with auditable traces and separate accounting for model runs and software simulations. The later assistant semantic reviews remain explicitly unvalidated, with no independent human labels. Róbert Lakatos supervised the research direction and reviewed the manuscript. RGB data, the Mistral checkpoint and software dependencies are external inputs.',
    }
    for index, value in replacements.items():
        p[index].text = value
    p[115]._p.getparent().remove(p[115]._p)

    def before(anchor, text, style=None):
        paragraph = doc.add_paragraph(text, style)
        anchor._p.addprevious(paragraph._p)
        return paragraph

    def caption(anchor, text):
        paragraph = before(anchor, text)
        paragraph.paragraph_format.keep_with_next = True
        paragraph.paragraph_format.space_before = Pt(7)
        paragraph.paragraph_format.space_after = Pt(4)
        for run in paragraph.runs:
            run.bold = True
        return paragraph

    def table(anchor, rows):
        t = doc.add_table(rows=0, cols=len(rows[0]))
        for values in rows:
            for c, value in zip(t.add_row().cells, values):
                c.text = str(value)
        anchor._p.addprevious(t._tbl)
        return t

    before(p[92], '3.7 Restricted neuro-symbolic verification', 'Heading 2')
    before(p[92], 'The implemented prototype targets a finite event-winner relation with explicit event and year constraints. A neural extractor produces typed question and source facts with quoted spans. Strict post-generation checks reject invalid JSON, incompatible types and unverifiable spans. This is validation after generation, not schema-constrained decoding. Source-polarity and coverage checks restrict which relations may support a decision. Valid quotations alone do not establish faithful semantic extraction.')
    before(p[92], 'The candidate obtains the answer claim from a separate finite-grammar parser that cannot inspect the source documents. It then checks this claim against validated source facts and question constraints. Explicit contradiction can produce REFUTED, mutually incompatible evidence CONFLICT, and insufficient or invalid extraction UNKNOWN. Only VERIFIED releases the unchanged generated draft; every other verdict returns the canonical abstention. This policy cannot introduce a new assertion, but can withhold a correct answer.')
    before(p[92], 'The extractor still receives the draft and emits a neural answer field, which the candidate decision replaces. The whole model call is therefore not source-independent. The rule layer checks consistency within its accepted representations; it has no external truth oracle or evidence of source credibility. A fictional reference winner is available only to evaluation, never to model generation or verification.')

    anchor = p[131]
    before(anchor, '5.8 Restricted verification and a negative generated-answer pilot', 'Heading 2')
    before(anchor, 'Early authored probes exposed false confirmations caused by relation and answer-claim interpretation. Deterministic guards blocked known development failures, but the prospective 45-case primary transfer reduced oracle-relative false confirmations from seven to zero while retaining only 18/24 correct decisive decisions (75%). This failed the joint 80% retention screen. All three false-source controls still passed. Oracle agreement measures consistency with an authored rule task, not real-world factual accuracy.')
    before(anchor, 'The subsequent 40-question generated-answer pilot evaluated the whole release policy. Standard RAG produced 25 correct, 11 wrong and four abstained answers; same-model review produced 25 correct and 15 wrong. The hybrid produced 17 correct, four wrong and 19 abstentions. It removed seven scored errors but withheld eight correct drafts, retaining 17/25 (68%). Mean utility fell from 0.350 to 0.325. The predeclared utility and retention screen failed, and all four false-source-only answers remained wrong and VERIFIED. Exact entity-name ambiguities and the finite answer contract further limit interpretation.')
    caption(anchor, 'Table 6. Generated-answer development pilot on 40 fictional questions.')
    table(anchor, [
        ['System', 'Correct', 'Wrong', 'Abstain', 'Utility'],
        ['Standard RAG', '25', '11', '4', '0.350'],
        ['Same-model review', '25', '15', '0', '0.250'],
        ['Original hybrid', '17', '4', '19', '0.325'],
    ])
    before(anchor, '5.9 Diagnosing context-dependent answer transcription', 'Heading 2')
    before(anchor, 'A polarity-aware development prompt improved exact extraction from 8/16 to 12/16 cases. Its combination with a new source audit gained three correct decisive verdicts but lost one correct REFUTED verdict, failing the no-regression gate. In a separate probe, four fixed answer identities were each paired with four source contexts. Both frozen prompts matched the intended answer claim in 12/16 contexts. All 32 answer quotations were exact, yet the extracted status or value changed with the sources. Exact span validation therefore did not ensure faithful answer transcription.')
    before(anchor, 'An offline correction replaced the extracted answer with a finite-grammar claim derived without source access, preserving the validated neural question and facts. This restored the known refutation without another loss among the tested correct decisive outcomes. Both the old UNKNOWN decision and the restored REFUTED decision withheld that answer, so the repair did not itself improve released-answer utility. The correction passed only a development gate for fresh transfer. Its apparent perfect transcription on the fixed probe follows from removing source access, not independent extraction validation.')
    before(anchor, '5.10 Prospective generated-answer transfer', 'Heading 2')
    before(anchor, 'The frozen transfer study used 24 new authored fictional questions across six mechanism families and completed 72 local model calls without retries or case replacement. The same standard-RAG draft was shared by the original and candidate hybrids. The candidate combines revised extraction instructions, a source audit and the independent answer component. The experiment therefore tests this bundle rather than isolating one component.')
    caption(anchor, 'Table 7. Frozen exact-score outcomes on 24 fictional transfer questions.')
    table(anchor, [
        ['Outcome', 'Standard RAG', 'Original hybrid', 'Candidate hybrid'],
        ['Correct', '14', '6', '12'],
        ['Wrong', '6', '4', '4'],
        ['Abstain', '0', '14', '8'],
        ['Unscorable', '4', '0', '0'],
        ['Mean utility', '[0.167, 0.500]', '0.083', '0.333'],
        ['Answer coverage', '[83.3%, 100%]', '41.7%', '66.7%'],
    ])
    before(anchor, 'Relative to the original hybrid, the candidate recovered four correct answers from paraphrased sources and two from sources with a negated distractor. It retained 12/14 correct standard-RAG drafts (85.7%). Both hybrids withheld every conflicting-source draft, including two correct standard-RAG answers. All four false-source-only controls were released as wrong answers by both hybrids. The candidate had 16 VERIFIED, four CONFLICT and four UNKNOWN verdicts; schema validation accepted all 24 extractions, which does not imply semantic correctness.')
    before(anchor, 'The primary candidate-versus-standard-RAG screen is INCONCLUSIVE. Four standard-RAG responses violated the exact answer contract; they remain UNSCORABLE rather than being relabelled wrong or abstained. The full-denominator paired utility difference is bounded by [−0.167, +0.167]. The frozen protocol did not permit its planned bootstrap intervals with unscorable outputs, so no interval or p-value was added retrospectively. The fully observed hybrid-to-hybrid utility difference is +0.250 within this fixture. It is not a population-effect estimate or proof of hallucination reduction.')
    caption(anchor, 'Table 8. Measured transfer latency including the shared draft in each hybrid arm.')
    table(anchor, [
        ['System', 'Mean s', 'Median s', 'p95 s', 'Calls per question'],
        ['Standard RAG', '0.352', '0.259', '0.765', '1'],
        ['Original hybrid', '5.480', '5.230', '6.404', '2'],
        ['Candidate hybrid', '5.563', '5.258', '6.802', '2'],
    ])
    before(anchor, 'The run used an Apple M5 Pro MacBook Pro with 24 GB unified memory. Across 72 actual calls it consumed 66,508 input and 13,032 output tokens, with 256.559 s summed model-call time. Model loading took 1.569 s and is excluded from the table. Peak MLX process allocation was 5.081 GB, not isolated memory per arm or whole-system RAM. The draft was generated once; adding arm totals would double-count shared work. The candidate does not demonstrate computational savings.')
    before(anchor, '5.11 Exploratory semantic review', 'Heading 2')
    before(anchor, 'A retrospective assistant review examined all 72 arm outputs as 38 distinct question-context-response records. The reviewer had seen the results, was not independent or blinded, and no human-reviewed labels were completed. Conditional on these unvalidated judgments, seven standard-RAG outputs and four outputs from each hybrid contained a false target-winner claim. Three exact-format failures were negative statements without a winner; the fourth extrapolated an incorrect winner to a new year. This separates incomplete answers from false assertions without changing the original primary labels.')
    before(anchor, 'All four false-source controls were judged both supported by the supplied evidence and false relative to the authored world. Source support and factual truth therefore cannot be treated as interchangeable. These exploratory labels are not a validated hallucination rate, do not support semantic significance tests, and do not resolve the inconclusive primary comparison. The review packet, blank human template, explicit assistant labels and original-to-derived record mapping remain separate artifacts.')

    before(p[135], '6.1 Local RAG Red-Team Arena', 'Heading 2')
    before(p[135], 'The Arena now provides recorded examples, local generation for three system variants, an editable attack passage with six templates, optional model-generated attacks, and a graph of actual rule decisions and quoted source spans. The interface exposes extraction failures and UNKNOWN outcomes alongside refutations. A SQLite ledger separates live rounds, archived examples and explicitly simulated software checks; local admission limits and a QR entry link support demonstration preparation.')
    before(p[135], 'Local acceptance includes 154 passing Python tests, browser checks, 100 explicitly simulated stored rounds and 20 simultaneous read-only browser sessions. These are software checks, not 100 model experiments or a model-throughput benchmark. Actual smoke tests include one three-call comparison and one four-call attack workflow. In the latter, standard RAG abstained, same-model review answered wrongly, and the hybrid abstained after invalid extraction. This was neither a symbolic refutation nor an improvement over standard RAG. Venue reachability, the final demonstration collection, audience effectiveness and a video remain unverified.')

    # Preserve the distinction between historical variants and the later hybrid.
    row = doc.tables[0].add_row()
    for c, value in zip(row.cells, ['Restricted hybrid', 'Neural extraction and deterministic release rules', 'Fictional pilots completed; not selective S4']):
        c.text = value
    mapping = doc.tables[-1]
    # New tables were appended to the XML before section 6, so locate by header.
    mapping = next(t for t in doc.tables if t.cell(0, 0).text == 'Identifier')
    for identifier, purpose in [
        ('EXP-030/031', 'Supplemental lexical metrics and blank independent-review materials'),
        ('EXP-032–035', 'Restricted extraction prototype and development rule guards'),
        ('EXP-036', 'Prospective synthetic transfer; joint retention screen failed'),
        ('EXP-037–039', 'Annotation materials and unvalidated assistant semantic analysis'),
        ('EXP-040', '40-question generated-answer pilot; utility/retention screen failed'),
        ('EXP-041/042', 'Polarity development and fixed-answer context diagnosis'),
        ('EXP-043', 'Offline source-independent answer component; development only'),
        ('EXP-044', '24-question frozen transfer; primary comparison inconclusive'),
        ('EXP-045', 'Retrospective assistant semantic review; no independent human labels'),
        ('EXP-046', 'Proposed 240-question automatic study; not frozen or run'),
        ('DEMO-M1–M5', 'Local Arena implementation and software acceptance, not efficacy tests'),
    ]:
        cells = mapping.add_row().cells
        cells[0].text, cells[1].text = identifier, purpose

    appendix_b = before(p[152], 'Appendix B. Dataset provenance', 'Heading 1')
    appendix_b.paragraph_format.page_break_before = True
    before(p[152], 'The local RGB files below were verified byte-for-byte against chen700564/RGB at upstream commit 65ec39e40e7dc9abb50e9bf1b4f32be3f6f16615. The upstream data license is CC BY-NC-SA 4.0. It does not establish a project-code license. Record counts describe task subsets rather than interchangeable train/test splits.')
    caption(p[152], 'Table B1. Local RGB files, record counts and SHA-256 digests.')
    table(p[152], [
        ['File and role', 'Records', 'SHA-256'],
        ['en_refine.json\nNoise development and same-question transfer', '300', '1be6ec4b85364b5590c7683ed4df8d475\n35ae21bc021bbcd3f44a71579f64bcb'],
        ['en_fact.json\nCounterfactual new-question test', '100', '92f4b2330ee407f74fbd923197028ef514\n0cfbc1f4b4092efec2d4d10ae6c9e5'],
        ['en_int.json\nNo model result claimed', '100', 'ab824393a15bb3e0a6b2c9037c8b50f28\n65874fc7984091ffdec1961f9b37bdf'],
    ])
    before(p[152], 'The fictional generated-answer fixtures are separately versioned in data/synthetic; the experiment-specific frozen manifests identify their exact hashes. References define fictional unique winners and do not attest real events. The proposed next fixture does not yet exist.')

    # Keep the reference's formal A4 / Times New Roman / 1.5 spacing layout.
    for name in ['Normal', 'Title', 'Heading 1', 'Heading 2']:
        doc.styles[name].font.color.rgb = RGBColor(0, 0, 0)
    for t in doc.tables:
        first = t.cell(0, 0).text
        widths = {
            'Variant': [2.0, 6.2, 7.8],
            'Noise level': [3, 8, 5],
            'Tag': [1.4, 9.0, 2.2, 3.4],
            'System / experiment': [5.2, 2.4, 2.4, 6.0],
            'Evidence stratum': [4.4, 5.8, 5.8],
            'Identifier': [3.0, 13.0],
            'Outcome': [5.2, 3.6, 3.6, 3.6],
            'File and role': [5.9, 1.4, 8.7],
        }.get(first, [6, 2.5, 2.5, 2.5, 2.5])
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        for column, width in zip(t.columns, widths):
            column.width = Cm(width)
        props = t._tbl.tblPr
        borders = props.find(qn('w:tblBorders'))
        if borders is not None:
            props.remove(borders)
        borders = OxmlElement('w:tblBorders')
        for edge in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            e = OxmlElement('w:' + edge)
            for key, value in [('val', 'single'), ('sz', '4'), ('color', 'D9D9D9')]:
                e.set(qn('w:' + key), value)
            borders.append(e)
        props.append(borders)
        for ri, row in enumerate(t.rows):
            trpr = row._tr.get_or_add_trPr()
            if trpr.find(qn('w:cantSplit')) is None:
                trpr.append(OxmlElement('w:cantSplit'))
            if ri == 0 and trpr.find(qn('w:tblHeader')) is None:
                trpr.append(OxmlElement('w:tblHeader'))
            for ci, (cell, width) in enumerate(zip(row.cells, widths)):
                cell.width = Cm(width)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                cpr = cell._tc.get_or_add_tcPr()
                shading = cpr.find(qn('w:shd'))
                if shading is None:
                    shading = OxmlElement('w:shd')
                    cpr.append(shading)
                shading.set(qn('w:fill'), 'E7E6E6' if ri == 0 else 'FFFFFF')
                margins = OxmlElement('w:tcMar')
                for edge in ['top', 'left', 'bottom', 'right']:
                    m = OxmlElement('w:' + edge)
                    m.set(qn('w:w'), '75')
                    m.set(qn('w:type'), 'dxa')
                    margins.append(m)
                cpr.append(margins)
                for para in cell.paragraphs:
                    para.paragraph_format.line_spacing = 1.05
                    para.paragraph_format.space_after = Pt(1 if first == 'Identifier' else 3)
                    para.paragraph_format.space_before = Pt(1 if first == 'Identifier' else 3)
                    para.paragraph_format.keep_with_next = ri == 0
                    para.alignment = WD_ALIGN_PARAGRAPH.LEFT if ci == 0 or first in ['Variant', 'Identifier', 'File and role'] else WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.font.name = 'Times New Roman'
                        run.font.size = Pt(9.5 if first == 'Identifier' else (10 if first != 'File and role' else 9))
                        run.font.color.rgb = RGBColor(0, 0, 0)
                        run.bold = ri == 0

        following = t._tbl.getnext()
        if following is not None and following.tag == qn('w:p'):
            from docx.text.paragraph import Paragraph
            Paragraph(following, doc._body).paragraph_format.space_before = Pt(8)

    # New compact TOC is populated from final rendered pagination in a second pass.
    for old in p[12:46]:
        old._p.getparent().remove(old._p)
    headings = [x for x in doc.paragraphs if x.style.name in ['Heading 1', 'Heading 2'] and x.text != 'Contents']
    for heading in headings:
        toc = before(p[46], heading.text + '\t0')
        toc.paragraph_format.line_spacing = 1
        toc.paragraph_format.space_after = Pt(1)
        toc.paragraph_format.left_indent = Cm(.35 if heading.style.name == 'Heading 2' else 0)
        toc.paragraph_format.tab_stops.add_tab_stop(Cm(15.7), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        for run in toc.runs:
            run.font.size = Pt(9.5)
            run.bold = heading.style.name == 'Heading 1'
    doc.core_properties.title = p[3].text
    doc.core_properties.author = 'Kirill Tarasov'
    doc.core_properties.subject = 'TDK research manuscript with results through EXP-045'
    doc.save(OUTPUT)


def update_pages(path):
    page_map = json.loads(Path(path).read_text())
    doc = Document(OUTPUT)
    in_contents = False
    for paragraph in doc.paragraphs:
        if paragraph.text == 'Contents':
            in_contents = True
        elif paragraph.text == 'Abstract' and paragraph.style.name == 'Heading 1':
            break
        elif in_contents:
            heading = paragraph.text.rsplit('\t', 1)[0]
            if heading not in page_map:
                raise ValueError(f'Missing page for {heading}')
            paragraph.runs[0].text = heading + '\t' + str(page_map[heading])
    doc.save(OUTPUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pages')
    args = parser.parse_args()
    if args.pages:
        update_pages(args.pages)
    else:
        if OUTPUT.exists():
            raise FileExistsError(OUTPUT)
        build()
    print(OUTPUT)
