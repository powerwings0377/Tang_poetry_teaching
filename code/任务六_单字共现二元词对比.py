# -*- coding: utf-8 -*-
"""
任务六：单字共现二元词的四诗人对比（图5系列：酒／雨／花／月）
================================
做什么：
  对 config.CHAR_TARGETS 里的每个单字（默认 酒、雨、花、月），分别在四位诗人
  的语料中找出与该字在同一首诗中共现的二元词（756 意象库），按 NPMI 排序，
  取前 CHAR_TOP_K 个进行对比，每个字出一张 2×2 四诗人对比图。

规则（与任务四自我网络完全同一口径）：
  - 共现单位：诗级——二元词与目标字出现在同一首诗即算共现，
    与"故人"自我网络的统计标准统一，全论文一致；
  - 邻居须与目标字至少共现 CHAR_MIN_CO 首诗（默认 2）；
  - config.EXCLUDE 里的非诗意功能词不作为邻居出现；
  - CHAR_EXCLUDE_CONTAINS = True 时，剔除包含目标字自身的二元词
    （如"酒"剔除"酒杯"），因为包含关系是平凡共现，会霸榜；
    想看目标字组成了哪些词，把它改成 False 重跑即可。

输出（output/任务六/）——为写论文准备的详细数据：
  - 共现对比_汇总.csv         全部四字的完整长表：目标字、诗人、排名、二元词、
                              英文、NPMI、共现诗数、二元词诗频、目标字诗频、情感值
  - 共现对比_摘要.txt         每个字 × 每位诗人的目标字诗频与占比、前10邻居速览、
                              四诗人 top3 并排对照（写对比段落直接用）
  - 图5_酒_共现对比_EN/CN.png、图5_雨_*.png、图5_花_*.png、图5_月_*.png（均含 PDF 版）

运行：python 任务六_单字共现二元词对比.py   （约1-2分钟）
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
    单字 target_char 的共现二元词（诗级 NPMI，与任务四自我网络同一口径：
    二元词与目标字出现在同一首诗即算共现）。
    config.EXCLUDE 里的非诗意功能词不作为邻居出现（被剔除后由后续名次递补）。
    返回 (结果列表, 诗作总数, 目标字诗频)；
    结果列表 = [(二元词, NPMI, 共现诗数, 二元词诗频, 情感值), ...]
    """
    n_poem = len(poem_texts)
    char_df = 0          # 含目标字的诗数
    bg_df = Counter()    # 含各二元词的诗数
    co = Counter()       # 同时含二元词与目标字的诗数
    for text in poem_texts:
        couplets = utils.split_into_couplets(text)
        has_c = any(target_char in coup for coup in couplets)
        if has_c:
            char_df += 1
        present = set()
        for coup in couplets:
            for bg in vocab:
                if bg in config.EXCLUDE:            # 非诗意功能词不入邻居
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
    out = utils.task_outdir('任务六_单字共现二元词对比')

    poems = utils.load_corpus()
    char_val, bi_val = utils.load_dicts()
    vocab = set(bi_val.keys())
    poet_poems = {n: [t for a, _, t in poems if a == n] for n in config.POETS}

    all_rows = []
    summary = []
    # results[目标字][诗人] = (邻居列表, 窗口总数, 目标字联频)
    results = {}

    for ch in config.CHAR_TARGETS:
        results[ch] = {}
        summary.append(f'\n{"=" * 60}\n目标字：{ch}（{config.TRANS.get(ch, "")}）\n{"=" * 60}')
        for n in config.POETS:
            net, n_poem, ch_df = char_cooccur(poet_poems[n], ch, vocab, bi_val)
            results[ch][n] = (net, n_poem, ch_df)
            summary.append(
                f'\n【{n}】诗作总数 {n_poem}，含"{ch}"的诗 {ch_df} 首'
                f'（占 {100 * ch_df / n_poem:.1f}%）')
            summary.append('  前{}邻居: '.format(len(net)) + ', '.join(
                f'{bg}({config.TRANS.get(bg, "")}, NPMI={npmi:+.3f}, 共现{co}首, 情感{v:+.2f})'
                for bg, npmi, co, bdf, v in net))
            for rank, (bg, npmi, co, bdf, v) in enumerate(net, 1):
                all_rows.append([ch, config.TRANS.get(ch, ''), n, config.POET_EN[n],
                                 rank, bg, config.TRANS.get(bg, ''), round(npmi, 4),
                                 co, bdf, ch_df, n_poem, round(v, 4)])
        # 四诗人 top3 并排速览
        summary.append('\n  四诗人 top3 并排:')
        for i in range(3):
            line = f'    第{i + 1}名: '
            for n in config.POETS:
                net = results[ch][n][0]
                line += f'{n}={net[i][0]}({net[i][1]:+.2f})  ' if i < len(net) else f'{n}=—  '
            summary.append(line)

    pd.DataFrame(all_rows, columns=['目标字', '目标字英文', '诗人', 'Poet', '排名',
                                    '二元词', '英文', 'NPMI', '共现诗数',
                                    '二元词诗频', '目标字诗频', '诗人诗作总数', '情感值']
                 ).to_csv(f'{out}/共现对比_汇总.csv', index=False, encoding='utf-8-sig')
    with open(f'{out}/共现对比_摘要.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary))
    print('\n'.join(summary[:8]))

    # ---------- 画图：每个字一张 2×2 四诗人对比 ----------
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
            fig.savefig(f'{out}/图5_{ch}_共现对比_{lang.upper()}.png', dpi=300)
            fig.savefig(f'{out}/图5_{ch}_共现对比_{lang.upper()}.pdf')
            plt.close(fig)
        print(f'{ch}: 图已生成')

    print(f'\n全部结果已保存到: {out}')


if __name__ == '__main__':
    main()
