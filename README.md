# Tang Poetry Feature–Evidence Teaching Paradigm: Data & Code Repository

This repository accompanies the paper *From impression to evidence: a
feature-evidence paradigm for teaching Tang poetic style and literary history*.
It contains the full analysis pipeline, intermediate data products, and all
paper figures, so that every number and every figure in the paper can be
reproduced, reloaded, or extended. **All files in this archive are in English.**
(Note: the corpus texts and the dictionary keys are classical Chinese poems and
words — these are the data objects under study and necessarily remain in
Chinese.)

---

## 1. Repository structure

```
Tang_poetry_teaching/
├── README.md                  ← this file
├── code/                      ← all analysis scripts, ready to run
│   ├── config.py              ← global configuration: paths, seeds, exclusions, thresholds, word lists
│   ├── utils.py               ← shared utilities
│   ├── task01_data_preparation_period_assignment.py
│   ├── task02_poet_style_analysis.py
│   ├── task03_period_trends_trajectories.py
│   ├── task04_shared_matrix_ego_networks.py
│   ├── task05_textbook_canon.py
│   ├── task06_char_cooccurrence.py
│   ├── task07_poet_networks.py            (supplementary exploration, not used in the paper)
│   ├── task08_period_networks.py          (supplementary exploration, not used in the paper)
│   ├── task09_robustness_checks.py        (threshold + seed sensitivity)
│   └── README.md              ← program usage guide
├── input/                     ← input data (see Section 4)
├── data/                      ← intermediate data products
│   ├── networks/              ← imagery networks of the four poets: node tables, edge tables, gexf
│   ├── validation_records/    ← validation records behind Section 4.6 (see INDEX.md there)
│   ├── robustness_checks/     ← Task-9 outputs: threshold_sensitivity.txt, seed_sensitivity.txt
│   ├── textbook_canon_108_scoring.csv
│   └── results_summary.json
└── figures/                   ← the nine paper figures, one folder per figure (EN versions)
```

---

## 2. Requirements

- Python ≥ 3.8; packages: `pandas numpy matplotlib openpyxl scipy networkx`
- Optional: `adjustText` (only for the non-overlapping labels of the volcano
  plot in Task 2, which is not used in the final paper; the script runs without it)
- Optional: Gephi for the network files (`data/networks/*_network.gexf` open
  directly in Gephi)

```bash
pip install pandas numpy matplotlib openpyxl scipy networkx adjustText
```

---

## 3. Quick start

```bash
cd code
python task01_data_preparation_period_assignment.py
python task02_poet_style_analysis.py
python task03_period_trends_trajectories.py
python task04_shared_matrix_ego_networks.py
python task05_textbook_canon.py
python task06_char_cooccurrence.py
python task09_robustness_checks.py
```

Each task writes its outputs to `code/output/<task>/`. Tasks 7–8 (network
analysis) are supplementary explorations not used in the final paper.

---

## 4. Input data

| File | Content | Notes |
|---|---|---|
| `input/tang_poems_cleaned.txt` | Cleaned Complete Tang Poems corpus, 41,821 poems | Format: `author#title#text`, one poem per line; source: gushiwen.cn, cleaned of volume markers, titles, annotations; traditional characters converted to simplified |
| `input/char_values_extended.txt` | Emotional-value dictionary of 7,050 characters | Columns: character, extended value, raw value, window frequency |
| `input/imagery_values_extended.txt` | Emotional-value dictionary of 756 core poetic imageries | Columns: imagery, value (including constituent-character contributions; may exceed [−1, 1]) |
| `input/poet_years_detailed.xlsx` | Birth/death years and period assignment of 338 poets | Assignment rules in Section 4.2 of the paper (hierarchical rule set) |
| `input/textbook_items_110.csv` | 110 Tang-poem items in the centrally compiled textbooks | 108 items matched into the canon corpus |

The seed sets (50 positive, 50 negative) live in `config.py` (`POS_SEEDS` /
`NEG_SEEDS`), identical to Supplementary Appendix A of the paper.

---

## 5. Paper-to-artifact map

| Paper content | Producing script | Data / figure file |
|---|---|---|
| Figure 1 paradigm architecture | PowerPoint Drawing | `figures/Figure1_framework/` |
| Figure 2 four-poet boxplots | Task 2 | `figures/Figure2_boxplots_four_poets/` |
| Figure 3 signature imageries (12×4) | Task 2 | `figures/Figure3_signature_imageries/` |
| Figure 4 shared-imagery matrix | Task 4 | `figures/Figure4_shared_imagery_matrix/` |
| Figure 5 companions of 酒 (wine) | Task 6 | `figures/Figure5_wine_cooccurrence/` |
| Figure 6 companions of 故人 (old friend) | Task 4 (ego networks) | `figures/Figure6_oldfriend_cooccurrence/` |
| Figure 7 dynasty-level emotional curve | Task 3 | `figures/Figure7_dynasty_curve/` |
| Figure 8 imagery trajectories (panels a/b) | Task 3 + Task 10 merge | `figures/Figure8_trajectories_ab/` |
| Figure 9 textbook canon vs. complete works | Task 5 | `figures/Figure9_canon_vs_corpus/` |
| Supplementary Table S1 (poet statistics & tests) | Task 2 | `code/output/task02*/` |
| Supplementary Table S2 (12 seed configurations) | Task 9 | `data/robustness_checks/seed_sensitivity.txt` |
| Threshold sensitivity (336 passing imageries) | Task 9, part A | `data/robustness_checks/threshold_sensitivity.txt` |
| Per-poem canon scoring | Task 5 | `data/textbook_canon_108_scoring.csv` |
| Validation records (expert annotation, gold standard, kappa) | — (original records) | `data/validation_records/` |
| Poet/period imagery networks (extended) | Tasks 7–8 | `data/networks/` |

---

## 6. Key numbers for verification

- Corpus 41,821 poems; 110,110 couplet windows; 1,021 BPE candidates; 756 core
  imageries retained at PCI ≥ 0.00
- Double-evidence filter (|v|≥0.3, |c1+c2|≥0.2, sign agreement): 336 imageries pass
- Imagery inventory vs. the literature-based gold standard: Cohen's kappa = 0.97
  (95% CI 0.93–1.00)
- Poem-level means: Li Bai +0.96, Wang Wei +0.79, Du Fu +0.68, Bai Juyi +0.67
- Period means: Early Tang +1.77, High +0.82, Mid +0.58, Late +0.53
  (F(3,36644) = 387.64)
- Textbook canon (108 poems) mean −0.03 (47.2% positive) vs. full corpus +0.75
  (68.5% positive)
- Seed sensitivity (12 resampled configurations): canon < corpus 12/12; Li Bai
  top-ranked 12/12; Early > High > Mid 12/12; Mid > Late 10/12

---

## 7. License & citation

- Code: MIT License
- Data and figures: CC BY 4.0 (please cite the source)

If you use this repository, please cite the paper (details to follow the
published version).

---

## 8. FAQ

- **Chinese characters show as boxes in figures?** Install any common Chinese
  font (Microsoft YaHei, SimHei, PingFang, etc.) and re-run the task.
- **Volcano-plot labels overlap?** Install `adjustText` and re-run Task 2
  (not used in the final paper).
- **Want to analyse other poets, periods, or words?** Edit only the word lists
  and parameters in `config.py` (`TRAJ_POS_WORDS`, `MATRIX_WORDS`,
  `CHAR_TARGETS`, `EXCLUDE`, etc.) and re-run the corresponding task; see
  `code/README.md`.
