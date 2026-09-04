# -*- coding: utf-8 -*-
"""
Task 4: Shared-imagery matrix and ego networks
==============================================
What it does:
  1. Shared-imagery matrix (paper Figure 4): each poet's corpus is retrained
     as an independent subcorpus, so every word in config.MATRIX_WORDS receives
     one value per poet within that poet's own context; cells with fewer than
     10 occurrences are starred (value rests on constituent characters alone).
  2. Ego networks (paper Figure 6): neighbours of config.EGO_TARGET in the
     corpora of config.EGO_POETS (rule: at least 2 shared poems, ranked by
     NPMI, top entries kept; non-poetic function words in config.EXCLUDE never
     appear as neighbours and are replaced by promotion).

Outputs (output/task04_matrix_ego/):
  - shared_imagery_matrix.csv (with occurrence counts and star marks)
  - figure4_shared_matrix_EN/CN.png
  - ego_network_neighbours.csv
  - figure6_ego_networks_EN/CN.png

Run: python task04_shared_matrix_ego_networks.py   (about 2-3 minutes)
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
    out = utils.task_outdir('task04_matrix_ego')

    poems = utils.load_corpus()
    char_val, bi_val = utils.load_dicts()
    vocab = set(bi_val.keys())
    poet_poems = {n: [t for a, _, t in poems if a == n] for n in config.POETS}

    # ---------- 1. Independent per-poet training -> matrix ----------
    print('=== 1. Independent training on each poet corpus ===')
    poet_bi_emo, poet_cnt = {}, {}
    for n in config.POETS:
        _, bi_emo, bigram_cnt, nwin = utils.train_subcorpus(poet_poems[n], vocab)
        poet_bi_emo[n], poet_cnt[n] = bi_emo, bigram_cnt
        print(f'{n}: trained, windows={nwin}')

    rows = []
    for w in config.MATRIX_WORDS:
        row = {'Imagery': w, 'English': config.TRANS.get(w, '')}
        for n in config.POETS:
            c = poet_cnt[n].get(w, 0)
            mark = '*' if c < config.MIN_BIGRAM_FREQ else ''
            row[n] = f'{poet_bi_emo[n].get(w, 0.0):+.4f}{mark}'
            row[f'{n}_count'] = c
        rows.append(row)
        print(w, {n: row[n] for n in config.POETS})
    pd.DataFrame(rows).to_csv(f'{out}/shared_imagery_matrix.csv', index=False, encoding='utf-8-sig')

    # ---------- Figure 4: matrix heatmap ----------
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
        fig.savefig(f'{out}/figure4_shared_matrix_{lang.upper()}.png', dpi=300)
        plt.close(fig)

    # ---------- 2. Ego networks ----------
    print('\n=== 2. Ego networks (paper Figure 6) ===')
    nets = {}
    rows = []
    for n in config.EGO_POETS:
        net = utils.ego_network(poet_poems[n], config.EGO_TARGET, vocab, bi_val)
        nets[n] = net
        print(f'[{n}]', ', '.join(f'{bg}({v:+.2f}, shared {co})' for bg, npmi, co, v in net))
        for bg, npmi, co, v in net:
            rows.append([n, bg, config.TRANS.get(bg, ''), round(npmi, 4), co, round(v, 4)])
    pd.DataFrame(rows, columns=['Poet', 'Neighbour', 'English', 'NPMI', 'Shared_poems', 'Value']
                 ).to_csv(f'{out}/ego_network_neighbours.csv', index=False, encoding='utf-8-sig')

    # ---------- Figure 6: ego networks (four poets, 2×2) ----------
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
        fig.suptitle('The same imagery, four lexical neighborhoods (edge width = NPMI; '
                     'red = positive neighbour, blue = negative)' if lang == 'en'
                     else '同一意象，两种词汇邻域（边宽＝NPMI；红＝正向邻居，蓝＝负向邻居）',
                     fontsize=13.5, y=0.97)
        plt.tight_layout(rect=[0, 0, 1, 0.93])
        fig.savefig(f'{out}/figure6_ego_networks_{lang.upper()}.png', dpi=300)
        plt.close(fig)

    print(f'\nAll results saved to: {out}')


if __name__ == '__main__':
    main()
