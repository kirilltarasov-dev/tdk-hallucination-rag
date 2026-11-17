# EXP-029 Disagreement Inspection

**Status:** Provisional qualitative inspection by the research assistant of
all 17 cases where at least one predeclared lexical diagnostic differed
between S1 and S3. This is not blinded independent human annotation, an
adjudicated semantic score, or an additional confirmatory hypothesis test.
The observations below are grounded in the exact predictions and ordered
documents in `results/raw/exp029_en_fact_counterfactual.jsonl`; full outputs
remain there. The benchmark's `answer` and `fakeanswer` fields identify
expected and constructed wrong values, but the correctness of all auxiliary
claims in a response has not been externally adjudicated.

| RGB ID | Stratum | Provisional reading of the paired outputs |
|---:|---|---|
| 1 | MIXED | Both name Norway correctly. S3 explicitly flags contradictory U.S. passages; S1 gives only the answer. |
| 7 | MIXED | Both name Andy Murray and reject Dominic Thiem. A singular/plural wording difference in the error phrase changes the literal marker, not the substantive answer. |
| 10 | MIXED | Both name Bianca Andreescu and identify the Emma Raducanu claim as wrong. The literal error marker differs only in wording. |
| 15 | WRONG_ONLY | S1 abstains but also states the benchmark-correct date while quoting the false passage. S3 asserts another wrong date, July 1, 2017. Neither is a clean supported answer; the true/fake string proxies are misleading. |
| 30 | MIXED | Both name James Cameron. S1 adds an unsupported explanation about a document attribution; S3 gives the direct answer. |
| 33 | MIXED | S1 first mentions the true 2020 date but ultimately calls the false 2010 date correct. S3 ultimately answers 2020. The true-answer substring proxy counts both. |
| 35 | MIXED | Both answer France. S1 discusses the conflicting Germany passages; S3 gives a direct answer. |
| 40 | WRONG_ONLY | S1 asserts an incorrect September 21, 2019 date. S3 first asserts the fake September 21, 2021 date, then gives the benchmark-correct September 20, 2019 date. The S3 response is internally contradictory. |
| 44 | MIXED | Both give March 3, 2017. S3 also identifies the false March 13, 2019 claim. |
| 50 | MIXED | S1 names Peter Handke, contrary to the benchmark answer Olga Tokarczuk. S3 abstains but still repeats Peter Handke as the 2018 winner; neither gives a clean correct answer. |
| 52 | WRONG_ONLY | S1 rejects the fake 2010 date but asserts another wrong date, June 9, 2020. S3 gives the benchmark-correct June 19, 2020 date and rejects the fake. This may reflect parametric knowledge because the selected context contains no correct passage. |
| 61 | MIXED | Both answer Mark Zuckerberg. S1 additionally discusses the Elon Musk passage; S3 answers directly. |
| 62 | MIXED | Both answer Elon Musk. S1 explicitly rejects the Mark Zuckerberg passage; S3 answers directly. |
| 72 | MIXED | Both give October 27, 2017. S1 explicitly flags the false 2016 passage; S3 answers directly. |
| 79 | MIXED | S1 answers Tabatha Rosproy and notes the conflict. S3 calls Juliana Urtubey the correct answer, contrary to the benchmark. |
| 84 | MIXED | S1 answers Dexter Fletcher, contrary to the benchmark's Bryan Singer answer. S3 abstains while mentioning Bryan Singer as initially attached; this is not a clean answer either. |
| 86 | MIXED | S1 abstains despite passages naming Tim Buckley as new CEO. S3 adopts the false Abigail Johnson claim. Both fail in different ways. |

The inspection shows why the lower S3 fake-answer substring count cannot be
interpreted as a lower false-assertion rate. A formal semantic comparison
requires a frozen annotation codebook, blind human labels, and adjudication
of ambiguous or internally contradictory responses. No such rate is reported
from this inspection.
