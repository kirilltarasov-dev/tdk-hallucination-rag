# RGB Dataset Provenance and Evaluation Roles

**Verified:** 2026-11-17. The three local files below are byte-identical to
the corresponding files in `chen700564/RGB` at upstream commit
`65ec39e40e7dc9abb50e9bf1b4f32be3f6f16615`. Counts refer to nonempty
JSONL records, not unique topics. The upstream repository's `LICENSE.txt`
specifies Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International (CC BY-NC-SA 4.0). This license applies to the upstream data;
it is not replaced by any license chosen for project code.

| Local file | Records | Bytes | SHA-256 | Role in this project |
|---|---:|---:|---|---|
| `data/rgb/en_refine.json` | 300 | 7,229,738 | `1be6ec4b85364b5590c7683ed4df8d47535ae21bc021bbcd3f44a71579f64bcb` | Development at 80% noise; a frozen 60%-noise condition-transfer test used the same questions. Not an independent-question test. |
| `data/rgb/en_fact.json` | 100 | 241,320 | `92f4b2330ee407f74fbd923197028ef5140cfbc1f4b4092efec2d4d10ae6c9e5` | New-question counterfactual set for prepared EXP-029. Input schema and contexts have been inspected; no model inference result exists yet. |
| `data/rgb/en_int.json` | 100 | 5,138,444 | `ab824393a15bb3e0a6b2c9037c8b50f2865874fc7984091ffdec1961f9b37bdf` | Information-integration subset. No project model result claimed. |

The upstream files and license can be retrieved from
`https://github.com/chen700564/RGB/tree/65ec39e40e7dc9abb50e9bf1b4f32be3f6f16615`.
The RGB benchmark paper is Chen et al., *Benchmarking Large Language Models
in Retrieval-Augmented Generation*, AAAI 2024, DOI
`10.1609/aaai.v38i16.29728`. The dataset describes task subsets, not a
single interchangeable train/test split: `en_refine` measures robustness
to noise, `en_int` information integration, and `en_fact` counterfactual
robustness.

`data/rgb/claim_routing_probe.json` is a local development probe and is not
one of the three upstream benchmark files listed above.

## Model and environment provenance

The completed MLX runs used the configured model name
`mlx-community/Mistral-7B-Instruct-v0.3-4bit`. The Hugging Face cache on the
audited machine currently contains snapshot
`a4b8f870474b0eb527f466a03fbc187830d271f5`. Historical raw results
record the model name but do not independently attest the exact downloaded
revision at run time. A future frozen run should record and load an explicit
revision; the current cache state must not be presented as proof of the
historical revision.

The current inference machine reports MacBook Pro `Mac17,8`, Apple M5 Pro,
18 CPU cores, and 24 GB unified memory. The project virtual environment has
Python 3.12, `mlx==0.32.2`, `mlx-lm==0.31.3`,
`transformers==5.17.0`, `huggingface_hub==1.33.0`, and
`numpy==2.5.3`. These are observed local versions; historic runs did not
record a complete dependency lock. Latency results should name this hardware
and keep assessment, generation, and routing stages separate.
