# Validation records (index)

This folder contains the original records behind the three validation checks
reported in Section 4.6 of the paper. All files are the primary evidence as
produced; Chinese-language fields are the original scholarly records.

| File | Content |
|---|---|
| `expert_annotation_1021_candidates.xlsx` | Expert annotation of all 1,021 candidate bigrams (three annotators with classical-literature backgrounds, negotiated-consensus protocol; 761 judged positive). Columns: rank, bigram, TAG (1 = imagery, 0 = not). |
| `gold_standard_stratified_sample_200.xlsx` | Stratified sample of 200 candidates (150 positive, 50 negative; random seed 2024) queried against the CNKI literature database for the gold-standard comparison (Cohen's kappa = 0.97). |
| `gold_standard_per_candidate_search_records.csv` | Per-candidate CNKI search records behind the gold-standard labelling (Chinese bibliographic citations, as retrieved). |
| `literature_reference_set_coverage_check.txt` | Coverage check of the 418-imagery reference set compiled from six peer-reviewed studies (coverage recall 100 percent over the 109 imageries with at least 100 corpus occurrences). |
| `literature_reference_set_frequency_table.txt` | Frequency table of the reference-set imageries used in the coverage check. |
