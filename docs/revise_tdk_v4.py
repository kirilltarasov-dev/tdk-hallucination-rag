"""Apply the first supervisor P0 corrections to the preserved v3 manuscript.

This creates a separate review draft. It does not change the approved title,
historical experiment records, or the already-sent v3 document.
"""

from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt


SOURCE = Path("deliverables/TDK_Research_Paper_v3_Kirill_Tarasov.docx")
OUTPUT = Path("deliverables/TDK_Research_Paper_v4_Kirill_Tarasov.docx")


def find(doc, prefix):
    matches = [p for p in doc.paragraphs if p.text.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one paragraph beginning {prefix!r}, got {len(matches)}")
    return matches[0]


def after(doc, anchor, text, style="Normal"):
    p = doc.add_paragraph(text, style=style)
    anchor._p.addnext(p._p)
    return p


def before(doc, anchor, text, style="Normal"):
    p = doc.add_paragraph(text, style=style)
    anchor._p.addprevious(p._p)
    return p


def remove(paragraph):
    paragraph._p.getparent().remove(paragraph._p)


def paragraph_index(paragraphs, target):
    return next(i for i, paragraph in enumerate(paragraphs) if paragraph._p is target._p)


def main():
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    doc = Document(SOURCE)

    # Clear the old static contents entries; page-checked entries are added
    # after the revised manuscript has been rendered once.
    contents = find(doc, "Contents")
    abstract_heading = next(p for p in doc.paragraphs if p.text == "Abstract" and p.style.name == "Heading 1")
    paragraphs = doc.paragraphs
    start, end = paragraph_index(paragraphs, contents), paragraph_index(paragraphs, abstract_heading)
    for paragraph in paragraphs[start + 1:end]:
        remove(paragraph)
    after(doc, contents, "[Contents will be populated after final pagination.]")

    find(doc, "TDK Research Paper — Supervisor Review Version").text = "TDK Research Paper"
    abstract = doc.paragraphs[paragraph_index(doc.paragraphs, abstract_heading) + 1]
    abstract.text = (
        "A fixed 4-bit Mistral-7B model was evaluated with benchmark-provided evidence on RGB. "
        "At 80% noise, standard RAG answered 268/300 questions under RGB-compatible lexical scoring. "
        "Hard evidence filtering reduced this to 251/300; restoring the original context when filtering removed every passage raised the score to 276/300. "
        "The hard-filter decline relative to standard RAG was paired-significant (18 fixed, 35 damaged; exact McNemar p=0.027), "
        "and safe fallback repaired 25 hard-filter outcomes without damaging any (p=5.96×10⁻⁸). "
        "These comparisons use a development condition and do not establish a general improvement. "
        "In a frozen transfer test at 60% noise on the same questions, safe-fallback filtering scored 290/300 against 294/300 for standard RAG. "
        "The results show a reproducible failure of aggressive filtering, a targeted correction, and the need to test evidence interventions beyond the data used to design them."
    )
    intro = find(doc, "This research focuses on these failure conditions")
    intro.text = (
        "This research examines how a fixed small language model responds to relevant and noisy external evidence. "
        "It measures the effects of standard retrieval-augmented generation, model-based self-verification, and document-level evidence filtering. "
        "The completed experiments diagnose when filtering removes useful evidence and test a specific fallback rule. "
        "A separate symbolic verification layer and end-to-end retrieval application require implementation and evaluation before they can support effectiveness claims."
    )
    find(doc, "The study uses a staged experimental design.").text = (
        "The completed systems comprise a question-only baseline (S0), standard RAG using RGB-provided passages (S1), "
        "a second model-based self-verification pass (S2), and document-level evidence filtering with either hard rejection or safe fallback (S3). "
        "A VERIFY/SKIP router was also evaluated on saved S2 drafts, followed by an offline policy simulation. "
        "No combined end-to-end S4 system or symbolic verifier has been evaluated."
    )
    status = {
        "S0": "Completed question-only baseline",
        "S1": "Completed RGB noise curve",
        "S2": "Completed model-based self-verification",
        "S3": "Completed at 80% and 60% noise; 80% was development",
        "S4": "Router and offline simulation only; end-to-end system pending",
    }
    systems = doc.tables[0]
    for row in systems.rows[1:]:
        row.cells[2].text = status[row.cells[0].text]

    find(doc, "All principal 80%-noise comparisons use").text = (
        "All principal 80%-noise comparisons use the same 300 RGB en_refine questions, model checkpoint, "
        "five benchmark-provided passages, and deterministic Random(2333) passage shuffle. "
        "Saved standard-RAG answers are text-identical to the self-verification drafts and share the same evidence contexts. "
        "The routing simulation and paired statistical analysis reuse saved responses without additional inference; their processed summaries contain input-file hashes."
    )
    find(doc, "EXP-008 and EXP-014–024 influenced").text = (
        "Exploratory diagnosis, assessor development, and fallback design used the 80%-noise condition. "
        "Consequently, all results at that condition are development evidence, including their paired p-values. "
        "The frozen 60%-noise transfer run used the same 300 questions with a different evidence composition; it is not an independent-question test. "
        "Final generalization claims require evaluation on new questions."
    )
    find(doc, "At 80% noise, RGB supplies one benchmark-positive").text = (
        "At 80% noise, RGB supplies one benchmark-positive and four benchmark-negative documents per question. "
        "The assessor independently labels each passage DIRECT, INFERENTIAL, TOPICAL, or NO_SUPPORT using only that passage and the question. "
        "The hard filter keeps the first two classes; when none survive, it emits the benchmark abstention phrase without a generation call. "
        "The safe-fallback policy reuses those assessments but restores the original ordered five-passage context in that empty-context branch. "
        "All other generation settings remain the same."
    )
    find(doc, "The taxonomy is multi-label").text = (
        "The taxonomy is multi-label, so one response may receive several tags. Among 29 semantic errors, "
        "27 (93.1%) were labelled relevant-evidence miss, 18 (62.1%) false abstention, "
        "10 (34.5%) distractor hijacking, 10 (34.5%) temporal or entity confusion, and four (13.8%) unsupported inference. "
        "At 80% noise, every question had one benchmark-positive passage. The model failed to use that available passage in 27 of the 29 semantic-error cases. "
        "The other two semantic errors had different primary failure labels."
    )
    taxonomy = doc.tables[2]
    taxonomy.add_column(Cm(2.0))
    taxonomy.cell(0, 3).text = "Percentage"
    for i, value in enumerate(("93.1%", "34.5%", "62.1%", "34.5%", "13.8%", "9.4%"), 1):
        taxonomy.cell(i, 3).text = value
    after(doc, find(doc, "The taxonomy is multi-label"),
          "Percentages for M1–M5 use 29 semantic errors; E1 uses all 32 lexical failures. Labels can overlap.")

    find(doc, "The first end-to-end S3 intervention").text = (
        "The hard-filter intervention retained only documents labelled DIRECT or INFERENTIAL. "
        "At 80% noise it scored 251/300 (83.67%), compared with 268/300 (89.33%) for standard RAG. "
        "Paired analysis found 18 FIXED and 35 DAMAGED outcomes (exact two-sided McNemar p=0.0270). "
        "The damaged cases retained 0.40 documents on average; 25 of 35 had an empty filtered context. "
        "These development data identify a concrete risk: false-negative support decisions can remove all evidence and force an incorrect abstention."
    )
    find(doc, "EXP-021 therefore changed").text = (
        "Safe fallback changed only the empty-context intervention while reusing the same passage assessments. "
        "With any DIRECT or INFERENTIAL passage retained, it used the filtered context; with none, it restored the original five passages. "
        "The score was 276/300 (92.00%) at 80% noise. Relative to standard RAG, it fixed 18 and damaged 10 cases, "
        "a net gain of eight (+2.67 percentage points; p=0.1849). Relative to hard filtering, it repaired 25 outcomes without damage "
        "(exact p=5.96×10⁻⁸). All 31 fallback cases were either CORRECT_UNCHANGED (25) or WRONG_UNCHANGED (6) relative to standard RAG: "
        "fallback prevented empty-context damage but did not itself fix a standard-RAG error. These are development-condition results."
    )
    doc.tables[3].cell(3, 0).text = "S3 Hard Filter"
    doc.tables[3].cell(4, 0).text = "S3 Safe Fallback"
    find(doc, "EXP-023 developed").text = (
        "A VERIFY/SKIP router was developed on a 25-case stratified probe and then applied to all 300 saved self-verification drafts. "
        "It received question, evidence, and draft, without gold labels in its input. It selected VERIFY 47 times and SKIP 253 times. "
        "Mean routing latency was 2.073 s per question, compared with 1.613 s for universal verification alone. "
        "The reduction in verifier calls therefore does not establish a reduction in total computation."
    )
    find(doc, "EXP-025 is an offline").text = (
        "The saved router decisions and verifier outputs were combined in an offline counterfactual simulation. "
        "SKIP retained the draft and VERIFY used the historical verifier final. The simulated score was 269/300 (89.67%), "
        "with two S1 errors fixed and one correct S1 answer damaged. It implies 47 verifier calls, but no combined end-to-end run or latency measurement exists."
    )
    find(doc, "EXP-026 applied").text = (
        "Paired exact McNemar tests and question-level percentile bootstrap intervals were calculated on saved development outputs. "
        "Self-verification fixed three and damaged two cases relative to standard RAG (+0.33 percentage points; p=1.000). "
        "Safe-fallback filtering fixed 18 and damaged 10 (+2.67 points; p=0.1849; bootstrap 95% interval [−0.67, 6.00] points). "
        "The offline routing policy fixed two and damaged one (+0.33 points; p=1.000). "
        "The hard-filter decline (p=0.0270) and safe-fallback rescue relative to hard filtering (p=5.96×10⁻⁸) are also paired results, "
        "but these p-values describe a reused development condition. They do not establish performance on unseen questions."
    )

    # Add the completed, frozen transfer result as a distinct section.
    examples = find(doc, "5.5 Illustrative paired cases")
    transfer = before(doc, examples, "5.5 Transfer to a lower-noise condition", "Heading 2")
    transfer = after(doc, transfer, (
        "The frozen safe-fallback policy was run without tuning on the same 300 RGB en_refine questions at 60% noise, "
        "with two benchmark-positive and three benchmark-negative passages per question. Standard RAG scored 294/300 (98.00%); "
        "safe-fallback filtering scored 290/300 (96.67%). The intervention fixed four and damaged eight paired responses, "
        "a −1.33 percentage-point difference (exact McNemar p=0.3877; paired bootstrap 95% interval [−3.67, 1.00] points). "
        "Filtering kept 505/600 benchmark-positive and 129/900 benchmark-negative passages; it restored the original context in 15 questions. "
        "Six of the eight DAMAGED responses retained at least one benchmark-negative passage, and two discarded both positive passages. "
        "This negative point estimate does not establish a general decline, but it does not support a general filtering benefit. "
        "Because the questions were used during development at another noise level, this is condition transfer rather than independent-question validation."
    ))
    examples.text = "5.6 Illustrative paired cases"

    # Place unbuilt application and symbolic work in Future Work.
    practical = find(doc, "5.6 Practical application")
    remove(doc.paragraphs[paragraph_index(doc.paragraphs, practical) + 1])
    remove(practical)
    find(doc, "The current S2 and S4 components use").text = (
        "The self-verification pass and routing component both use the same language model as the generator. "
        "No deterministic symbolic verifier or measured neuro-symbolic outcome exists yet. "
        "The present experiments therefore support claims about evidence filtering and model-based verification only."
    )
    find(doc, "The completed experiments establish a controlled baseline").text = (
        "The completed work identifies an empty-context failure of hard filtering and tests a targeted safe fallback. "
        "At 80% noise, standard RAG scored 268/300, hard filtering 251/300, and safe fallback 276/300. "
        "The significant hard-filter and fallback-rescue comparisons are development results. "
        "At 60% noise, the unchanged safe-fallback policy scored 290/300 against 294/300 for standard RAG, with uncertainty spanning zero. "
        "The evidence does not establish a general improvement or a neuro-symbolic verification result."
    )
    conclusion = find(doc, "The completed work identifies")
    conclusion = after(doc, conclusion, "RQ1 — Partially answered: standard RAG fell from 99.67% at 0% noise to 89.33% at 80% noise on the controlled RGB curve; 100% noise was a separate negative-rejection task.")
    conclusion = after(doc, conclusion, "RQ2 — Answered within development data: 29 semantic failures at 80% noise were manually reviewed; 27 involved failure to use an available relevant passage, with overlapping failure categories.")
    conclusion = after(doc, conclusion, "RQ3 — Partially answered: hard filtering damaged standard RAG, while safe fallback repaired 25 hard-filter outcomes. Safe fallback did not show a statistically established gain over standard RAG and scored lower at 60% noise.")
    after(doc, conclusion, "RQ4 — Not yet answered: an offline routing simulation used 47 potential verifier calls, but routing time exceeded the historical verifier time and no end-to-end selective system was measured.")
    references = find(doc, "References")
    future = before(doc, references, "8. Future Work", "Heading 1")
    future = after(doc, future, (
        "The next test should use new questions with conflicting evidence and a frozen policy. The prepared RGB en_fact protocol separates mixed correct/wrong evidence from wrong-only contexts; no model result is claimed yet. "
        "A genuine neuro-symbolic extension would extract typed facts and question constraints, then apply written deterministic rules to accept, refute, flag conflict, or return UNKNOWN. "
        "Extraction quality and end-to-end effects must be measured before the extension can support the thesis title."
    ))
    after(doc, future, (
        "A proposed RAG Red-Team Arena would let visitors insert misleading passages and compare system answers with an auditable rule trace. "
        "The demonstrator, real retrieval index, independent test sets, and human-validated semantic metrics remain future work."
    ))

    own = find(doc, "The project-specific code and experiment scripts")
    own.text = (
        "I developed the project-specific experiment scripts and controlled comparisons in the accompanying research repository. "
        "I implemented and evaluated the no-retrieval, standard-RAG, self-verification, and evidence-filtering variants; manually reviewed high-noise failures; "
        "identified the empty-context failure; and tested the safe-fallback correction and its transfer to 60% noise. "
        "I also conducted the routing study and offline simulation, with their limitations reported above. "
        "Róbert Lakatos supervised the research direction and reviewed the manuscript. "
        "RGB data, the Mistral checkpoint, and software dependencies are external inputs."
    )
    # The repository has no verified public remote URL yet; do not invent one.

    # Number and caption all existing tables. Their order is unchanged.
    captions = (
        "Table 1. Evaluated system variants and completion status.",
        "Table 2. Standard RAG performance across RGB evidence-noise conditions.",
        "Table 3. Multi-label failure taxonomy at 80% noise. M1–M5 percentages use 29 semantic errors; E1 uses 32 lexical failures.",
        "Table 4. Development-condition system scores at 80% noise.",
    )
    for table, caption in zip(doc.tables, captions):
        p = doc.add_paragraph(caption)
        table._tbl.addprevious(p._p)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(7)
        p.paragraph_format.space_after = Pt(3)
        for run in p.runs:
            run.bold = True
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
        if table is taxonomy:
            for row in table.rows:
                row.cells[0].width = Cm(1.0)
                row.cells[1].width = Cm(8.0)
                row.cells[2].width = Cm(1.5)
                row.cells[3].width = Cm(2.0)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
