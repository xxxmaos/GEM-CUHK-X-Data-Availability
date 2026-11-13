GEM: reviewer results and analysis package
=========================================

Public review version: v1.0-review. This package provides frozen numerical
predictions, analysis code, generated figures, and dataset access documentation.
No credentials or access to the private development repository are needed to
recompute the supplied result tables and figures.

Quick start
-----------

Tested with Python 3.14.3. From a clean checkout::

    python -m pip install -r requirements.txt
    python verify_results.py
    python analysis/figure/generate_results_figures.py

The first command installs dependencies. The remaining commands run offline,
without model calls, source images, checkpoints, or API keys. The verification
checks SHA-256 file integrity and recomputes metrics for the supplementary
offline controls (1,046 clips), evidence interventions (120 clips), and paired
cost comparison (60 clips). The plotting script checks primary predictions,
accuracy, macro-F1, corrections/harms, acceptance, paired bootstrap intervals,
and AURC, then produces seven PDF/SVG/PNG figures and four LaTeX tables under
analysis/figure/. Bootstrap uses 2,000 subject-level resamples with seed 42.

Files and scope
---------------

* analysis/results1046_snapshot_20261030T093341Z/: primary and guard-ablation results.
* analysis/completed_experiments_20261101/: reinspection, robustness and model-composition results.
* analysis/reviewer_revision_results_20261104/: simple controls, interventions and cost results.
* analysis/figure/: executable plotting source and regenerated result artifacts.
* DATA_DICTIONARY.txt: field meanings and interpretation.
* bundle_provenance.json and SHA256SUMS.json: copied source provenance and release integrity.
* verification_report.json: outcome and environment of the local reproduction check.
* DATASET_INFO.txt, ACCESS_AND_LICENSE.txt, dataset_reference.bib: upstream dataset documentation.
* data_availability.tex: editable manuscript availability statement.

This is reproduction of analyses from frozen predictions, not end-to-end
retraining or rerunning the multimodal agents. Original observations, sampled
frames, model weights, response text, and full request caches are not included.
The original development repository remains private.

Interpretation
--------------

The historical 1,046-clip cohort is exploratory; source records document
upstream subject overlap and post-observation rule selection. Recomputing fixed
predictions does not establish independent generalization or repeated-run
stability. Subset cost measurements concern only the paired 60-clip experiment.
See the supplied independence audit and original summary boundary fields.

Dataset access
--------------

CUHK-X -- Small Model Track (HAR training release).
Official project: https://openaiotlab.github.io/CUHK-X/
Release: https://huggingface.co/datasets/Kevin-Pal/CUHK-X_Small_Model_Track
License: https://huggingface.co/datasets/Kevin-Pal/CUHK-X_Small_Model_Track/blob/main/LICENSE
Original data must be obtained from its owners under their access conditions.
This repository is not a mirror of CUHK-X and does not grant rights to its data.

Repository: https://github.com/xxxmaos/GEM-CUHK-X-Data-Availability
Frozen release: https://github.com/xxxmaos/GEM-CUHK-X-Data-Availability/releases/tag/v1.0-review
