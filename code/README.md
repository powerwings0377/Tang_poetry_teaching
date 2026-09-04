# Code guide

Ten task-structured Python scripts reproduce every number, table, and figure in
the paper. Edit `config.py` to change word lists, thresholds, or targets; re-run
the corresponding task.

## Layout

- `config.py` — global configuration: paths, seed sets, exclusions, thresholds, word lists
- `utils.py` — shared utilities (data loading, couplet segmentation, scoring, training, tests)
- `task01_data_preparation_period_assignment.py`
- `task02_poet_style_analysis.py`
- `task03_period_trends_trajectories.py`
- `task04_shared_matrix_ego_networks.py`
- `task05_textbook_canon.py`
- `task06_char_cooccurrence.py`
- `task07_poet_networks.py` — supplementary exploration, not used in the paper
- `task08_period_networks.py` — supplementary exploration, not used in the paper
- `task09_robustness_checks.py` — threshold + seed sensitivity (paper Sections 4.4 and 4.6)
- `input/` — input data (see the root README, Section 4)

## Run

```bash
pip install pandas numpy matplotlib openpyxl adjustText networkx scipy
cd code
python task01_data_preparation_period_assignment.py
python task02_poet_style_analysis.py
python task03_period_trends_trajectories.py
python task04_shared_matrix_ego_networks.py
python task05_textbook_canon.py
python task06_char_cooccurrence.py
python task09_robustness_checks.py
python task10_figure_utilities.py
```

Each task writes its outputs to `code/output/<task>/`. Approximate runtimes:
task 1 seconds; task 2 about 1–2 min; task 3 about 3–5 min (four independent
trainings); task 4 about 2–3 min; task 5 about 1 min; task 6 about 1–2 min;
task 9 about 1 min (part B traverses the corpus once).

## Paper-to-task map

See the root README, Section 5.
