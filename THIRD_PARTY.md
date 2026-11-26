# Third-party materials

The project code is available under the MIT license in `LICENSE`. That license
does not relicense third-party datasets, model weights, or dependencies.

The files `data/rgb/en_refine.json`, `data/rgb/en_fact.json` and
`data/rgb/en_int.json` are byte-identical to selected files from the RGB
benchmark by Chen et al. at upstream commit
`65ec39e40e7dc9abb50e9bf1b4f32be3f6f16615`. The benchmark's
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(CC BY-NC-SA 4.0) license applies to them. Its license text is retained in
`data/rgb/LICENSE_RGB.txt`; hashes and provenance are in
`docs/dataset_manifest.md`. Researchers using the RGB data must follow that
license, including its attribution, noncommercial and share-alike terms.

The pinned Mistral model and other packages are external dependencies. Model
weights are not stored in this repository. Their respective licenses apply
when downloaded or used. Research outputs containing excerpts from RGB remain
subject to the applicable upstream rights; the MIT project-code license does
not override those rights.
