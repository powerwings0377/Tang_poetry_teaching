# -*- coding: utf-8 -*-
"""
任务二：四诗人风格分析
================================
做什么：
  1. 四位诗人（config.POETS）的每首诗打分，得诗级情感分布（表1 + 图1箱线图）；
  2. 六对韦尔奇 t 检验 + 霍姆校正（表1注释的数字来源）；
  3. 签名意象表（表2 + 图2条形图）与高频意象表（附录C），
     均经双重证据过滤 + 非诗意功能词筛查（config.EXCLUDE）。

输出（output/任务二/）：
  - 表1_四诗人情感分布.csv、表1_两两检验.csv
  - 表2_签名意象.csv、附录C_高频意象.csv
  - 图1_四诗人箱线图_EN/CN.png、图2_签名意象_EN/CN.png、图3_火山图_EN/CN.png

运行：python 任务二_四诗人风格分析.py   （约1-2分钟）
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
    out = utils.task_outdir('任务二_四诗人风格分析')

    poems = utils.load_corpus()
    char_val, bi_val = utils.load_dicts()
    vocab = set(bi_val.keys())

    poet_poems = {n: [t for a, _, t in poems if a == n] for n in config.POETS}
    poet_npoem = {n: len(v) for n, v in poet_poems.items()}

    # ---------- 1. 诗级打分与分布 ----------
    print('=== 1. 诗级情感分布（表1）===')
    score_arr = {}
    rows = []
    for n in config.POETS:
        vals = [v for v in (utils.analyze_poem(t, char_val, bi_val)
                            for t in poet_poems[n]) if v is not None]
        score_arr[n] = np.array(vals)
        a = score_arr[n]
        rows.append([n, len(a), a.mean(), np.median(a), a.std(ddof=1)])
        print(f'{n}: n={len(a)}  均值={a.mean():+.4f}  中位数={np.median(a):+.4f}  标准差={a.std(ddof=1):.4f}')
    pd.DataFrame(rows, columns=['诗人', '诗作数', '平均情感值', '中位数', '标准差']
                 ).to_csv(f'{out}/表1_四诗人情感分布.csv', index=False, encoding='utf-8-sig')

    # ---------- 2. 两两检验 ----------
    print('\n=== 2. 韦尔奇两两检验（霍姆校正）===')
    df_test = utils.welch_all_pairs(score_arr)
    print(df_test.round(4).to_string(index=False))
    df_test.to_csv(f'{out}/表1_两两检验.csv', index=False, encoding='utf-8-sig')

    # ---------- 3. 签名意象表与高频意象表 ----------
    print('\n=== 3. 词表构建（双重证据过滤 + 诗意筛查）===')
    poet_img_cnt = {n: utils.count_imageries(poet_poems[n], vocab) for n in config.POETS}
    sig = {n: utils.signature_list(n, poet_img_cnt, poet_npoem, char_val, bi_val)
           for n in config.POETS}
    hf = {n: utils.highfreq_list(n, poet_img_cnt, char_val, bi_val)
          for n in config.POETS}
    for n in config.POETS:
        print(f'【{n}】签名:', '、'.join(x[0] for x in sig[n]))
        print(f'【{n}】高频:', '、'.join(x[0] for x in hf[n]))

    # 保存为对照表（每位诗人一列）
    pd.DataFrame({n: [f'{x[0]}({x[1]}, {x[2]:.1f}, {x[3]:+.2f})' for x in sig[n]]
                  for n in config.POETS}
                 ).to_csv(f'{out}/表2_签名意象.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame({n: [f'{x[0]}({x[1]}, {x[2]:+.2f})' for x in hf[n]]
                  for n in config.POETS}
                 ).to_csv(f'{out}/附录C_高频意象.csv', index=False, encoding='utf-8-sig')

    # ---------- 图1：箱线图 ----------
    for lang in ['en', 'cn']:
        fig, ax = plt.subplots(figsize=(9, 6))
        colors = ['#f2b5c0', '#a8c6e0', '#aad4b5', '#f5dfa8']
        data = [score_arr[n] for n in config.POETS]
        bp = ax.boxplot(data, patch_artist=True, widths=0.55,
                        medianprops=dict(color='black', lw=2),
                        flierprops=dict(marker='o', ms=3, alpha=.35, color='gray'))
        for patch, c in zip(bp['boxes'], colors):
            patch.set_facecolor(c)
        means = [d.mean() for d in data]
        ax.scatter(range(1, 5), means, marker='D', s=90, color='#a01818', zorder=5,
                   label='Mean' if lang == 'en' else '均值')
        for i, m in enumerate(means):
            ax.annotate(f"{'mean' if lang=='en' else '均值'} {m:+.2f}",
                        (i + 1.28, m + 0.05), color='#a01818', fontsize=12, fontweight='bold')
        ax.axhline(0, ls='--', color='gray', lw=1)
        labels = [f'{config.POET_EN[n]}\n({len(score_arr[n]):,})' if lang == 'en' else n
                  for n in config.POETS]
        ax.set_xticklabels(labels, fontsize=12)
        ax.set_ylabel('Poem-level emotional value' if lang == 'en' else '诗级情感值', fontsize=13)
        ax.legend(fontsize=11, loc='upper right')
        ax.grid(alpha=.25)
        ax.set_axisbelow(True)
        plt.tight_layout()
        fig.savefig(f'{out}/图1_四诗人箱线图_{lang.upper()}.png', dpi=300)
        plt.close(fig)

    # ---------- 图2：签名意象条形图（每人12条） ----------
    for lang in ['en', 'cn']:
        fig, axes = plt.subplots(2, 2, figsize=(17, 10))
        for ax, n in zip(axes.flat, config.POETS):
            entries = sig[n]
            names = [f"{bg} ({config.TRANS.get(bg, '')})" if lang == 'en' else bg
                     for bg, c, r, v in entries]
            counts = [c for _, c, _, _ in entries]
            vals = [v for _, _, _, v in entries]
            cols = [RED if v > 0 else BLUE for v in vals]
            y = list(range(len(entries)))[::-1]
            ax.barh(y, counts, color=cols, alpha=.85)
            ax.set_yticks(y)
            ax.set_yticklabels(names, fontsize=10.5)
            for yi, c, v in zip(y, counts, vals):
                ax.text(c + 0.4, yi, f'{v:+.2f}', va='center', fontsize=9.5,
                        color=RED if v > 0 else BLUE, fontweight='bold')
            ax.set_title(f"{config.POET_EN[n]} (n = {poet_npoem[n]:,})" if lang == 'en'
                         else f'{n}（{poet_npoem[n]}首）', fontsize=15, fontweight='bold')
            ax.set_xlabel('Occurrences' if lang == 'en' else '出现次数', fontsize=11)
            ax.grid(axis='x', alpha=.25)
            ax.set_axisbelow(True)
            ax.set_xlim(0, max(counts) * 1.22)
        fig.suptitle('Signature imageries of the four poets (double-evidence filtered; '
                     'red = positive, blue = negative)' if lang == 'en'
                     else '四诗人签名意象（双重证据过滤；红＝正，蓝＝负）', fontsize=15, y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.98])
        fig.savefig(f'{out}/图2_签名意象_{lang.upper()}.png', dpi=300)
        plt.close(fig)

    # ---------- 图3：火山图 ----------
    for lang in ['en', 'cn']:
        fig, axes = plt.subplots(2, 2, figsize=(16, 11))
        for ax, n in zip(axes.flat, config.POETS):
            xs, ys, ss = [], [], []
            others_n = sum(poet_npoem[o] for o in config.POETS if o != n)
            for bg, c in poet_img_cnt[n].items():
                others = sum(poet_img_cnt[o][bg] for o in config.POETS if o != n)
                ratio = (c / poet_npoem[n]) / (others / others_n) if others > 0 else 16
                xs.append(math.log2(max(ratio, 1e-6)))
                ys.append(bi_val[bg])
                ss.append(c)
            xs, ys, ss = np.array(xs), np.array(ys), np.array(ss)
            cols = [RED if y > 0 else BLUE for y in ys]
            ax.scatter(xs, ys, s=np.sqrt(ss) * 28, c=cols, alpha=.45,
                       edgecolors='white', lw=.4)
            ax.axhline(0, ls='--', color='gray', lw=1)
            ax.axvline(1, ls=':', color='gray', lw=1)
            # 标注该诗人的12个签名意象：英文版只标英文译名并用 adjustText 防重叠；
            # 中文版标"中文 (English)"。adjustText 未安装时退化为直接放置
            try:
                from adjustText import adjust_text
                _has_adj = True
            except ImportError:
                _has_adj = False
            texts = []
            for t in utils.signature_list(n, poet_img_cnt, poet_npoem, char_val, bi_val, topn=12):
                w, c = t[0], t[1]
                others = sum(poet_img_cnt[o][w] for o in config.POETS if o != n)
                ratio = (c / poet_npoem[n]) / (others / others_n) if others > 0 else 16
                lx = math.log2(max(ratio, 1e-6)); ly = bi_val[w]
                lab = config.TRANS.get(w, w) if lang == 'en' else f'{w} {config.TRANS.get(w, "")}'.strip()
                texts.append(ax.text(lx, ly, lab, fontsize=9.5, fontweight='bold', color='#333333'))
            if _has_adj:
                adjust_text(texts, ax=ax,
                            arrowprops=dict(arrowstyle='-', color='#999999', lw=0.6),
                            expand=(1.4, 2.2), force_text=(0.3, 0.6), force_points=(0.2, 0.4))
            ax.set_title(f"{config.POET_EN[n]} (n = {poet_npoem[n]:,})" if lang == 'en'
                         else f'{n}（{poet_npoem[n]}首）', fontsize=15, fontweight='bold')
            ax.set_xlabel('log2 frequency ratio (vs other three poets)' if lang == 'en'
                          else 'log2 频率比（相对其他三位诗人）', fontsize=11)
            ax.set_ylabel('Emotional value' if lang == 'en' else '情感值', fontsize=11)
            ax.grid(alpha=.25)
            ax.set_axisbelow(True)
        fig.suptitle('Volcano plots of imagery distinctiveness (red = positive, blue = negative; '
                     'bubble size = occurrences)' if lang == 'en'
                     else '意象区分度火山图（红＝正，蓝＝负；气泡大小＝出现次数）', fontsize=15, y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.98])
        fig.savefig(f'{out}/图3_火山图_{lang.upper()}.png', dpi=300)
        plt.close(fig)

    print(f'\n全部结果已保存到: {out}')


if __name__ == '__main__':
    main()
