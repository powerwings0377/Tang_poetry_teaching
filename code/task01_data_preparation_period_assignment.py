# -*- coding: utf-8 -*-
"""
Task 1: Data preparation and period assignment
==============================================
What it does:
  1. Loads tang_poems_cleaned.txt (author#title#text, one poem per line);
  2. Loads the "period" column of poet_years_detailed.xlsx (the result of the
     hierarchical rule set: literary-history consensus first -> longest span of
     the creative years (age 18-60) -> ties within 3 years go to the earlier
     period; unknown/dubious/non-Tang poets are not assigned to the four periods);
  3. Assigns each poem to one of the four periods via its author, and outputs
     the poem counts per period (the source of the numbers in Section 4.2).

Outputs (output/task01_data_preparation/):
  - poet_period_assignment.csv   one period per poet
  - period_poem_counts.txt       poem counts per period and the totals
                                 (cited in Section 4.2 of the paper)

Run: python task01_data_preparation_period_assignment.py
"""
from collections import Counter

import pandas as pd

import config
import utils


def main():
    poems = utils.load_corpus()
    name2period = utils.load_period_map()
    out = utils.task_outdir('task01_data_preparation')

    print(f'Total poems in the corpus: {len(poems)}')
    print(f'Total authors: {len(set(a for a, _, _ in poems))}')

    # assign each poem to a period via its author
    period_count = Counter()
    unassigned = 0
    for author, title, text in poems:
        p = name2period.get(author)
        if p in config.PERIODS:
            period_count[p] += 1
        else:
            unassigned += 1

    # save the assignment table
    df = pd.read_excel(config.POET_YEAR_FILE)
    df['时期_clean'] = (df['时期'].astype(str)
                      .str.replace('（文学史公认）', '', regex=False).str.strip())
    df.to_csv(f'{out}/poet_period_assignment.csv', index=False, encoding='utf-8-sig')

    with open(f'{out}/period_poem_counts.txt', 'w', encoding='utf-8') as f:
        f.write('Period\tPoems\n')
        for p in config.PERIODS:
            f.write(f'{p}\t{period_count[p]}\n')
        f.write(f'Total (assigned)\t{sum(period_count.values())}\n')
        f.write(f'Unassigned\t{unassigned}\n')

    print('\nPoem counts per period (cited in Section 4.2):')
    for p in config.PERIODS:
        print(f'  {p}: {period_count[p]}')
    print(f'  Total assigned: {sum(period_count.values())}, unassigned: {unassigned}')
    print(f'\nResults saved to: {out}')


if __name__ == '__main__':
    main()
