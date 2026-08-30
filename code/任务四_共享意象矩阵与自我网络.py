# -*- coding: utf-8 -*-
"""
任务四：共享意象矩阵与自我网络
================================
做什么：
  1. 共享意象矩阵（表3 + 图4热力图）：把每位诗人的语料作为独立子语料重训，
     config.MATRIX_WORDS 里的每个词在每位诗人处得到一个专属情感值；
     出现不足10次的格子标星号（数值仅来自构词字）。
  2. 自我网络（图5）：config.EGO_TARGET 中心词在 config.EGO_POETS
     四位诗人语料中的邻居网络（规则：诗级共现≥2首，按 NPMI 排序取前十；
     config.EXCLUDE 里的非诗意功能词不作为邻居出现，剔除后由后续名次递补）。

输出（output/任务四/）：
  - 表3_共享意象矩阵.csv（含出现次数与星号标记）
  - 图4_共享意象矩阵_EN/CN.png
  - 自我网络_邻居表.csv
  - 图5_自我网络_EN/CN.png

运行：python 任务四_共享意象矩阵与自我网络.py   （约2-3分钟）
"""
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config
import utils

RED, BLUE = '#d4574c', '#4a72a6'


def main():
    utils.setup_chinese_font()
    out = utils.task_outdir('任务四_共享意象矩阵与自我网络')

    poems = utils.load_corpus()
    char_val, bi_val = utils.load_dicts()
    vocab = set(bi_val.keys())
    poet_poems = {n: [t for a, _, t in poems if a == n] for n in config.POETS}

    # ---------- 1. 各诗人独立训练 → 矩阵 ----------
    print('=== 1. 各诗人语料独立训练 ===')
    poet_bi_emo, poet_cnt = {}, {}
    for n in config.POETS:
        _, bi_emo, bigram_cnt, nwin = utils.train_subcorpus(poet_poems[n], vocab)
        poet_bi_emo[n], poet_cnt[n] = bi_emo, bigram_cnt
        print(f'{n}: 训练完成，联数={nwin}')

    rows = []
    for w in config.MATRIX_WORDS:
        row = {'意象': w, '英文': config.TRANS.get(w, '')}
        for n in config.POETS:
            c = poet_cnt[n].get(w, 0)
            mark = '*' if c < config.MIN_BIGRAM_FREQ else ''
            row[n] = f'{poet_bi_emo[n].get(w, 0.0):+.4f}{mark}'
            row[f'{n}_次数'] = c
        rows.append(row)
        print(w, {n: row[n] for n in config.POETS})
    pd.DataFrame(rows).to_csv(f'{out}/表3_共享意象矩阵.csv', index=False, encoding='utf-8-sig')

    # ---------- 图4：矩阵热力图 ----------
    for lang in ['en', 'cn']:
        data = np.array([[poet_bi_emo[n].get(w, 0.0) for n in config.POETS]
                         for w in config.MATRIX_WORDS])
        counts = np.array([[poet_cnt[n].get(w, 0) for n in config.POETS]
                           for w in config.MATRIX_WORDS])
        fig, ax = plt.subplots(figsize=(9.5, 8))
        vmax = max(abs(data.min()), abs(data.max()))
        im = ax.imshow(data, cmap='RdBu_r', vmin=-vmax, vmax=vmax, aspect='auto')
        ax.set_xticks(range(4))
        ax.set_xticklabels([f'{n} ({config.POET_EN[n]})' for n in config.POETS], fontsize=11.5)
        ax.set_yticks(range(len(config.MATRIX_WORDS)))
        ax.set_yticklabels([f"{w} ({config.TRANS.get(w, '')})" for w in config.MATRIX_WORDS],
                           fontsize=10.5)
        for i in range(data.shape[0]):
            for j in range(4):
                v, c = data[i, j], counts[i, j]
                ax.text(j, i, f'{v:+.2f}' + ('*' if c < config.MIN_BIGRAM_FREQ else ''),
                        ha='center', va='center', fontsize=10,
                        color='white' if abs(v) > vmax * 0.55 else '#333')
        fig.text(0.12, 0.015,
                 '* Imagery occurs < 10 times in that poet\u2019s corpus; '
                 'value rests on constituent characters alone.' if lang == 'en'
                 else '* 该意象在该诗人语料中出现不足 10 次，数值仅来自构词字。',
                 fontsize=9, color='#666')
        ax.set_title('Emotional values of shared imageries, recomputed within '
                     'each poet\u2019s corpus' if lang == 'en'
                     else '共享意象在四位诗人各自语料中独立重算的情感值', fontsize=12.5)
        fig.colorbar(im, ax=ax,
                     label='Emotional value' if lang == 'en' else '情感值', shrink=.85)
        plt.tight_layout(rect=[0, 0.04, 1, 1])
        fig.savefig(f'{out}/图4_共享意象矩阵_{lang.upper()}.png', dpi=300)
        plt.close(fig)

    # ---------- 2. 自我网络 ----------
    print('\n=== 2. 自我网络（图5）===')
    nets = {}
    rows = []
    for n in config.EGO_POETS:
        net = utils.ego_network(poet_poems[n], config.EGO_TARGET, vocab, bi_val)
        nets[n] = net
        print(f'【{n}】', ', '.join(f'{bg}({v:+.2f},共{co}首)' for bg, npmi, co, v in net))
        for bg, npmi, co, v in net:
            rows.append([n, bg, config.TRANS.get(bg, ''), round(npmi, 4), co, round(v, 4)])
    pd.DataFrame(rows, columns=['诗人', '邻居词', '英文', 'NPMI', '共现诗数', '情感值']
                 ).to_csv(f'{out}/自我网络_邻居表.csv', index=False, encoding='utf-8-sig')

    # ---------- 图5：自我网络（四位诗人 2×2） ----------
    for lang in ['en', 'cn']:
        fig, axes = plt.subplots(2, 2, figsize=(15, 15))
        for ax, n in zip(axes.flat, config.EGO_POETS):
            net = nets[n]
            k = len(net)
            pos = {}
            for i, (bg, npmi, co, v) in enumerate(net):
                ang = 2 * math.pi * i / k + math.pi / 2
                pos[bg] = (0.60 * math.cos(ang), 0.60 * math.sin(ang))
            for bg, npmi, co, v in net:
                ax.plot([0, pos[bg][0]], [0, pos[bg][1]], color='#b9b9b9',
                        lw=max(npmi, 0.05) * 5, zorder=1)
            for bg, npmi, co, v in net:
                ax.scatter(*pos[bg], s=2600, color=RED if v > 0 else BLUE,
                           zorder=5, alpha=.92)
                ax.annotate(bg, pos[bg], ha='center', va='center', fontsize=13.5,
                            color='white', fontweight='bold', zorder=6)
                x, y_ = pos[bg]
                ax.annotate(f"({config.TRANS.get(bg, '')})", (x * 1.42, y_ * 1.42),
                            ha='center', va='center', fontsize=10.5, color='#333', zorder=6)
            ax.scatter(0, 0, s=3400, color='#6e6e6e', zorder=5)
            ax.annotate(config.EGO_TARGET, (0, 0), ha='center', va='center', fontsize=15,
                        color='white', fontweight='bold', zorder=6)
            ax.annotate(f"({config.TRANS.get(config.EGO_TARGET, '')})", (0, -0.155),
                        ha='center', va='center', fontsize=11.5, color='#333')
            ax.set_title(f"{config.POET_EN[n]}: ego-network of {config.EGO_TARGET} "
                         f"({config.TRANS.get(config.EGO_TARGET, '')})" if lang == 'en'
                         else f'{n}：“{config.EGO_TARGET}”自我网络',
                         fontsize=14, fontweight='bold')
            ax.axis('off')
            ax.set_xlim(-1.05, 1.05)
            ax.set_ylim(-1.0, 1.0)
        fig.suptitle('The same imagery, two lexical neighborhoods (edge width = NPMI; '
                     'red = positive neighbor, blue = negative)' if lang == 'en'
                     else '同一意象，两种词汇邻域（边宽＝NPMI；红＝正向邻居，蓝＝负向邻居）',
                     fontsize=13.5, y=0.97)
        plt.tight_layout(rect=[0, 0, 1, 0.93])
        fig.savefig(f'{out}/图5_自我网络_{lang.upper()}.png', dpi=300)
        plt.close(fig)

    print(f'\n全部结果已保存到: {out}')


if __name__ == '__main__':
    main()
