# -*- coding: utf-8 -*-
"""
任务一：数据准备与时期归属
================================
做什么：
  1. 读取《全唐诗_cleaned.txt》（作者#诗题#正文，一行一首）；
  2. 读取《诗人年份-详细.xlsx》中的"时期"列（即三级分层规则的归属结果：
     文学史共识优先 → 18-60岁创作期最长覆盖 → 相差≤3年归早期；
     未知/存疑/非唐人不入四期）；
  3. 把每首诗按作者归入四期，输出各期诗作数（论文4.2节的数字来源）。

输出（output/任务一/）：
  - 诗人时期归属.csv      每位诗人的时期
  - 各期诗作数.txt        四期诗作数与总计（论文4.2节引用）

运行：python 任务一_数据准备与时期归属.py
"""
from collections import Counter

import pandas as pd

import config
import utils


def main():
    poems = utils.load_corpus()
    name2period = utils.load_period_map()
    out = utils.task_outdir('任务一_数据准备与时期归属')

    print(f'语料诗作总数: {len(poems)}')
    print(f'作者总数: {len(set(a for a, _, _ in poems))}')

    # 每首诗按作者归期
    period_count = Counter()
    unassigned = 0
    for author, title, text in poems:
        p = name2period.get(author)
        if p in config.PERIODS:
            period_count[p] += 1
        else:
            unassigned += 1

    # 保存归属表
    df = pd.read_excel(config.POET_YEAR_FILE)
    df['时期_clean'] = (df['时期'].astype(str)
                      .str.replace('（文学史公认）', '', regex=False).str.strip())
    df.to_csv(f'{out}/诗人时期归属.csv', index=False, encoding='utf-8-sig')

    with open(f'{out}/各期诗作数.txt', 'w', encoding='utf-8') as f:
        f.write('时期\t诗作数\n')
        for p in config.PERIODS:
            f.write(f'{p}\t{period_count[p]}\n')
        f.write(f'合计(入四期)\t{sum(period_count.values())}\n')
        f.write(f'未入四期\t{unassigned}\n')

    print('\n各期诗作数（论文4.2节引用这组数字）:')
    for p in config.PERIODS:
        print(f'  {p}: {period_count[p]}')
    print(f'  合计入四期: {sum(period_count.values())}，未入四期: {unassigned}')
    print(f'\n结果已保存到: {out}')


if __name__ == '__main__':
    main()
