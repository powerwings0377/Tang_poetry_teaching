# -*- coding: utf-8 -*-
"""
Task 6: Character-level co-occurrence comparison across the four poets
(paper Figure 5 series: 酒 wine / 雨 rain / 花 flowers / 月 moon)
=====================================================================
What it does:
  For each single character in config.CHAR_TARGETS (default 酒, 雨, 花, 月),
  finds in each of the four poets' corpora the bigrams (from the 756-imagery
  inventory) that co-occur with the character within the same poem, ranks them
  by NPMI, and keeps the top CHAR_TOP_K for comparison, producing one 2×2
  four-poet figure per character.

Rules (identical to the ego-network construction of Task 4):
  - Co-occurrence unit: the poem — a bigram and the target character count as
    co-occurring when they appear in the same poem; the same standard is used
    throughout the paper;
  - Neighbours must share at least CHAR_MIN_CO poems with the target
    (default 2);
  - Non-poetic function words in config.EXCLUDE never appear as neighbours;
  - With CHAR_EXCLUDE_CONTAINS = True, bigrams containing the target character
    itself are dropped (e.g., 酒杯 for 酒), because containment is trivial
    co-occurrence and would dominate the ranking; set it False and re-run to
    inspect word formation instead.

Outputs (output/task06_char_cooccurrence/) — detailed data prepared for writing:
  - cooccurrence_full.csv    complete long table for all four characters:
                             target, poet, rank, bigram, English gloss, NPMI,
                             shared poems, bigram poem frequency, target poem
                             frequency, emotional value
  - cooccurrence_summary.txt per character x poet: target poem frequency and
                             share, top-10 neighbours, and a side-by-side top-3
                             comparison across the four poets
  - figure5_wine/rain/flowers/moon_cooccurrence_EN/CN.png (with PDF versions)

Run: python task06_char_cooccurrence.py   (about 1-2 minutes)
"""
import math
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt

import config
import utils

RED, BLUE = '#d4574c', '#4a72a6'


def char_cooccur(poem_texts, target_char, vocab, bi_val,
                 topk=config.CHAR_TOP_K, min_co=config.CHAR_MIN_CO,
                 exclude_contains=config.CHAR_EXCLUDE_CONTAINS):
    """
    Bigrams co-occurring with the single character target_char (poem-level NPMI,
    identical to the ego-network standard of Task 4: a bigram and the target
    count as co-occurring when they appear in the same poem).
    Non-poetic function words in config.EXCLUDE never appear as neighbours
    (removed and replaced by promotion).
    Returns (result list, total poems, target poem frequency);
    result list = [(bigram, NPMI, shared poems, bigram poem freq, value), ...]
    """
    n_poem = len(poem_texts)
    char_df = 0          # poems containing the target character
    bg_df = Counter()    # poems containing each bigram
    co = Counter()       # poems containing both a bigram and the target
    for text in poem_texts:
        couplets = utils.split_into_couplets(text)
        has_c = any(target_char in coup for coup in couplets)
        if has_c:
            char_df += 1
        present = set()
        for coup in couplets:
            for bg in vocab:
                if bg in config.EXCLUDE:            # non-poetic function words are never neighbours
                    continue
                if exclude_contains and target_char in bg:
                    continue
                if bg in coup:
                    present.add(bg)
        for bg in present:
            bg_df[bg] += 1
            if has_c:
                co[bg] += 1
    res = []
    for bg, c0 in co.items():
        if c0 < min_co:
            continue
        pb, pc, pbc = bg_df[bg] / n_poem, char_df / n_poem, c0 / n_poem
        npmi = math.log(pbc / (pb * pc)) / (-math.log(pbc))
        res.append((bg, npmi, c0, bg_df[bg], bi_val.get(bg, 0.0)))
    res.sort(key=lambda x: -x[1])
    return res[:topk], n_poem, char_df


def main():
    utils.setup_chinese_font()
    out = utils.task_outdir('task06_char_cooccurrence')

    poems = utils.load_corpus()
    char_val, bi_val = utils.load_dicts()
    vocab = set(bi_val.keys())
    poet_poems = {n: [t for a, _, t in poems if a == n] for n in config.POETS}

    all_rows = []
    summary = []
    # results[target][poet] = (neighbour list, total poems, target poem frequency)
    results = {}

    for ch in config.CHAR_TARGETS:
        results[ch] = {}
        summary.append(f'\n{"=" * 60}\nTarget character: {ch} ({config.TRANS.get(ch, "")})\n{"=" * 60}')
        for n in config.POETS:
            net, n_poem, ch_df = char_cooccur(poet_poems[n], ch, vocab, bi_val)
            results[ch][n] = (net, n_poem, ch_df)
            summary.append(
                f'\n[{n}] poems {n_poem}, poems containing "{ch}": {ch_df} '
                f'({100 * ch_df / n_poem:.1f}%)')
            summary.append(f'  top {len(net)} neighbours: ' + ', '.join(
                f'{bg}({config.TRANS.get(bg, "")}, NPMI={npmi:+.3f}, shared {co}, value {v:+.2f})'
                for bg, npmi, co, bdf, v in net))
            for rank, (bg, npmi, co, bdf, v) in enumerate(net, 1):
                all_rows.append([ch, config.TRANS.get(ch, ''), n, config.POET_EN[n],
                                 rank, bg, config.TRANS.get(bg, ''), round(npmi, 4),
                                 co, bdf, ch_df, n_poem, round(v, 4)])
        # side-by-side top-3 across the four poets
        summary.append('\n  Top 3 side by side:')
        for i in range(3):
            line = f'    No.{i + 1}: '
            for n in config.POETS:
                net = results[ch][n][0]
                line += f'{n}={net[i][0]}({net[i][1]:+.2f})  ' if i < len(net) else f'{n}=—  '
            summary.append(line)

    pd.DataFrame(all_rows, columns=['Target', 'Target_EN', 'Poet', 'Poet_EN', 'Rank',
                                    'Bigram', 'English', 'NPMI', 'Shared_poems',
                                    'Bigram_poems', 'Target_poems', 'Poet_poems', 'Value']
                 ).to_csv(f'{out}/cooccurrence_full.csv', index=False, encoding='utf-8-sig')
    with open(f'{out}/cooccurrence_summary.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary))
    print('\n'.join(summary[:8]))

    # ---------- figures: one 2×2 four-poet comparison per character ----------
    for ch in config.CHAR_TARGETS:
        for lang in ['en', 'cn']:
            fig, axes = plt.subplots(2, 2, figsize=(15, 15))
            for ax, n in zip(axes.flat, config.POETS):
                net, n_poem, ch_df = results[ch][n]
                k = max(len(net), 1)
                pos = {}
                for i, (bg, npmi, co, bdf, v) in enumerate(net):
                    ang = 2 * math.pi * i / k + math.pi / 2
                    pos[bg] = (0.60 * math.cos(ang), 0.60 * math.sin(ang))
                for bg, npmi, co, bdf, v in net:
                    ax.plot([0, pos[bg][0]], [0, pos[bg][1]], color='#b9b9b9',
                            lw=max(npmi, 0.05) * 5, zorder=1)
                for bg, npmi, co, bdf, v in net:
                    ax.scatter(*pos[bg], s=2600, color=RED if v > 0 else BLUE,
                               zorder=5, alpha=.92)
                    ax.annotate(bg, pos[bg], ha='center', va='center', fontsize=13.5,
                                color='white', fontweight='bold', zorder=6)
                    x, y_ = pos[bg]
                    ax.annotate(f"({config.TRANS.get(bg, '')})", (x * 1.42, y_ * 1.42),
                                ha='center', va='center', fontsize=10.5, color='#333',
                                zorder=6)
                ax.scatter(0, 0, s=3400, color='#6e6e6e', zorder=5)
                ax.annotate(ch, (0, 0), ha='center', va='center', fontsize=16,
                            color='white', fontweight='bold', zorder=6)
                ax.annotate(f"({config.TRANS.get(ch, '')})", (0, -0.155), ha='center',
                            va='center', fontsize=11.5, color='#333')
                ax.set_title(f"{config.POET_EN[n]} (n = {len(poet_poems[n]):,})"
                             if lang == 'en' else f'{n}（{len(poet_poems[n])}首）',
                             fontsize=14, fontweight='bold')
                ax.axis('off')
                ax.set_xlim(-1.05, 1.05)
                ax.set_ylim(-1.0, 1.0)
            ch_en = config.TRANS.get(ch, '')
            fig.suptitle(
                f'Co-occurring bigrams of the character {ch} ({ch_en}) in the four poets '
                f'(poem-level NPMI; red = positive, blue = negative)' if lang == 'en'
                else f'四位诗人与"{ch}"（{ch_en}）共现的二元词对比'
                     f'（诗级 NPMI；红＝正，蓝＝负）',
                fontsize=14, y=0.98)
            plt.tight_layout(rect=[0, 0, 1, 0.96])
            fname = config.TRANS.get(ch, ch).lower().replace(' ', '_')
            fig.savefig(f'{out}/figure5_{fname}_cooccurrence_{lang.upper()}.png', dpi=300)
            fig.savefig(f'{out}/figure5_{fname}_cooccurrence_{lang.upper()}.pdf')
            plt.close(fig)
        print(f'{ch}: figure generated')

    print(f'\nAll results saved to: {out}')


if __name__ == '__main__':
    main()
