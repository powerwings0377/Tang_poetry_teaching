# -*- coding: utf-8 -*-
"""
任务三：时期趋势与意象轨迹
================================
做什么：
  1. 王朝情感曲线（图6）：各期诗级情感均值、方差分析、线性趋势、Tukey 两两比较。
     配色方案在 config.py 的 FIG6_PALETTE 切换（'classic' 原版蓝 / 'warm' 暖赭 / 'forest' 深青金）；
  2. 意象轨迹拆成两张独立图：图7（正向，config.TRAJ_POS_WORDS）和图8（负向，
     config.TRAJ_NEG_WORDS）。各期子语料独立重训（论文4.4节口径）。
     ★ 换词方法：改 config.py 里的两个列表，重跑本任务。
     ★ 空心点 = 该期出现不足10次，数值仅来自构词字。

输出（output/任务三/）：
  - 王朝曲线_统计.txt      （各期 n/均值/标准差/正负比例 + 检验结果）
  - 意象轨迹_数值.csv      （每词 × 四期的情感值与出现次数）
  - 图6_王朝情感曲线_EN/CN.png、图7_意象轨迹_EN/CN.png、图8_意象轨迹_EN/CN.png（均含 PDF 版）

运行：python 任务三_时期趋势与意象轨迹.py   （约3-5分钟，要训练四次）
"""
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

import config
import utils


def main():
    utils.setup_chinese_font()
    out = utils.task_outdir('任务三_时期趋势与意象轨迹')

    poems = utils.load_corpus()
    char_val, bi_val = utils.load_dicts()
    vocab = set(bi_val.keys()) | set(config.TRAJ_WORDS)
    name2period = utils.load_period_map()

    period_texts = {p: [t for a, _, t in poems if name2period.get(a) == p]
                    for p in config.PERIODS}

    # ---------- 1. 王朝曲线 ----------
    print('=== 1. 王朝情感曲线（图6）===')
    period_scores = {}
    for p in config.PERIODS:
        vals = [v for v in (utils.analyze_poem(t, char_val, bi_val)
                            for t in period_texts[p]) if v is not None]
        period_scores[p] = np.array(vals)
    groups = [period_scores[p] for p in config.PERIODS]
    F, p_anova = stats.f_oneway(*groups)
    allv = np.concatenate(groups)
    grand = allv.mean()
    ss_between = sum(len(g) * (g.mean() - grand) ** 2 for g in groups)
    eta2 = ss_between / ((allv - grand) ** 2).sum()
    weights = np.array([-3, -1, 1, 3])
    means = np.array([g.mean() for g in groups])
    ns = np.array([len(g) for g in groups])
    sds = np.array([g.std(ddof=1) for g in groups])
    mse = sum((ns - 1) * sds ** 2) / (ns.sum() - 4)
    t_lin = (weights * means).sum() / math.sqrt(mse * (weights ** 2 / ns).sum())
    tukey = stats.tukey_hsd(*groups)

    with open(f'{out}/王朝曲线_统计.txt', 'w', encoding='utf-8') as f:
        f.write('时期\t诗作数\t平均情感值\t标准差\t积极诗%\t消极诗%\n')
        for p in config.PERIODS:
            a = period_scores[p]
            f.write(f'{p}\t{len(a)}\t{a.mean():.4f}\t{a.std(ddof=1):.4f}\t'
                    f'{100 * (a > 0).mean():.1f}\t{100 * (a < 0).mean():.1f}\n')
            print(f'{p}: n={len(a)}  均值={a.mean():+.4f}  标准差={a.std(ddof=1):.4f}')
        f.write(f'\nANOVA: F(3,{ns.sum() - 4}) = {F:.2f}, p = {p_anova:.2e}, eta2 = {eta2:.4f}\n')
        f.write(f'线性趋势: t = {t_lin:.2f}\n')
        f.write('\nTukey HSD 两两比较:\n')
        for i in range(4):
            for j in range(i + 1, 4):
                f.write(f'  {config.PERIODS[i]} vs {config.PERIODS[j]}: '
                        f'diff={means[i] - means[j]:+.4f}, p={tukey.pvalue[i, j]:.4f}\n')
    print(f'ANOVA: F(3,{ns.sum() - 4})={F:.2f}, eta2={eta2:.4f}, 线性趋势 t={t_lin:.2f}')
    print(f'中唐 vs 晚唐: p={tukey.pvalue[2, 3]:.4f}')

    # ---------- 2. 各期独立训练 + 意象轨迹 ----------
    print('\n=== 2. 各期独立训练并计算轨迹（图7）===')
    traj = {}
    for p in config.PERIODS:
        _, bi_emo, bigram_cnt, nwin = utils.train_subcorpus(period_texts[p], vocab)
        print(f'{p}: 训练完成，联数={nwin}')
        for w in config.TRAJ_WORDS:
            traj.setdefault(w, {})[p] = (bi_emo.get(w, 0.0), bigram_cnt.get(w, 0))

    rows = []
    for w in config.TRAJ_WORDS:
        for p in config.PERIODS:
            v, c = traj[w][p]
            rows.append([w, config.TRANS.get(w, ''), p, round(v, 4), c,
                         '是' if c < config.MIN_BIGRAM_FREQ else ''])
    pd.DataFrame(rows, columns=['意象', '英文', '时期', '情感值', '出现次数', '低于10次标记']
                 ).to_csv(f'{out}/意象轨迹_数值.csv', index=False, encoding='utf-8-sig')

    # ---------- 画图 ----------
    pal = config.PALETTES[config.FIG6_PALETTE]   # 图6配色方案（config.py 可切换）

    def spread_labels(ys, min_gap):
        ys = list(ys)
        order = sorted(range(len(ys)), key=lambda i: -ys[i])
        adj = ys[:]
        for _ in range(50):
            changed = False
            for a in range(len(order) - 1):
                i, j = order[a], order[a + 1]
                if adj[i] - adj[j] < min_gap:
                    mid = (adj[i] + adj[j]) / 2
                    adj[i] = mid + min_gap / 2
                    adj[j] = mid - min_gap / 2
                    changed = True
            if not changed:
                break
        return adj

    def draw_trajectory(words, fig_no, subtitle_en, subtitle_cn, lang):
        """单张轨迹图：words 列表里的词各一条线，红色区域为安史之乱后"""
        fig, ax = plt.subplots(figsize=(11.5, 6.8))
        ax.axvspan(1.5, 3.5, color=pal['band'], alpha=.6, zorder=0)
        x = np.arange(4)
        cmap = plt.get_cmap('tab10')
        colors = {w: cmap(k % 10) for k, w in enumerate(words)}
        for w in words:
            vals = [traj[w][p][0] for p in config.PERIODS]
            cnts = [traj[w][p][1] for p in config.PERIODS]
            ax.plot(x, vals, '-', color=colors[w], lw=2.4, zorder=2)
            for xi, (v, c) in enumerate(zip(vals, cnts)):
                if c >= config.MIN_BIGRAM_FREQ:
                    ax.scatter(xi, v, s=80, color=colors[w], zorder=3)
                else:
                    ax.scatter(xi, v, s=80, facecolors='white',
                               edgecolors=colors[w], linewidths=1.8, zorder=3)
        if words:
            endv = [traj[w]['晚唐'][0] for w in words]
            adj = spread_labels(endv, (max(endv) - min(endv)) * 0.08 + 0.15)
            for w, v0, va in zip(words, endv, adj):
                ax.plot([3.02, 3.14], [v0, va], color=colors[w], lw=0.9, alpha=.6)
                ax.annotate(f"{w} ({config.TRANS.get(w, '')})", (3.2, va),
                            color=colors[w], fontsize=11.5, fontweight='bold', va='center')
        ax.axhline(0, ls='--', color='gray', lw=1)
        ax.set_xticks(x)
        ax.set_xticklabels([config.PERIOD_EN[p] for p in config.PERIODS]
                           if lang == 'en' else config.PERIODS, fontsize=12)
        ax.set_xlabel('Tang period' if lang == 'en' else '唐代分期', fontsize=12)
        ax.set_ylabel('Emotional value' if lang == 'en' else '情感值', fontsize=12)
        ax.set_title(subtitle_en if lang == 'en' else subtitle_cn, fontsize=13.5)
        ax.text(2.5, ax.get_ylim()[1] * 0.94,
                'An Lushan Rebellion (755–763)' if lang == 'en' else '安史之乱 (755–763)',
                ha='center', fontsize=12, color=pal['label'], fontweight='bold')
        ax.text(-0.1, ax.get_ylim()[0] + 0.05,
                'Hollow markers: < 10 occurrences in that period (character-based value only).'
                if lang == 'en' else '空心点：该期出现不足 10 次，数值仅来自构词字。',
                fontsize=9, color='#666', va='bottom')
        ax.grid(alpha=.25)
        ax.set_axisbelow(True)
        ax.set_xlim(-0.15, 4.7)
        plt.tight_layout()
        fig.savefig(f'{out}/图{fig_no}_意象轨迹_{lang.upper()}.png', dpi=300)
        fig.savefig(f'{out}/图{fig_no}_意象轨迹_{lang.upper()}.pdf')
        plt.close(fig)

    for lang in ['en', 'cn']:
        # 图6：王朝曲线（新配色，可在 config.py 切换 FIG6_PALETTE）
        fig, ax = plt.subplots(figsize=(9, 6))
        means_l = [period_scores[p].mean() for p in config.PERIODS]
        sds_l = [period_scores[p].std(ddof=1) for p in config.PERIODS]
        x = range(4)
        ax.axvspan(1.5, 3.5, color=pal['band'], alpha=.6, zorder=0)
        ax.errorbar(x, means_l, yerr=sds_l, fmt='o-', color=pal['line'], lw=3, ms=12,
                    ecolor=pal['err'], elinewidth=3, capsize=8, capthick=3, zorder=3)
        for xi, m in zip(x, means_l):
            ax.annotate(f'{m:+.2f}', (xi - 0.06, m + 0.35), fontsize=14,
                        fontweight='bold', color=pal['line'])
        ax.text(2.5, 1.45, 'An Lushan Rebellion\n(755–763)' if lang == 'en'
                else '安史之乱\n(755–763)', ha='center', fontsize=13,
                color=pal['label'], fontweight='bold')
        years = ['618–712', '713–765', '766–835', '836–907']
        ax.set_xticks(list(x))
        ax.set_xticklabels([f'{config.PERIOD_EN[p]} Tang\n{y}' if lang == 'en'
                            else f'{p}\n{y}' for p, y in zip(config.PERIODS, years)],
                           fontsize=12)
        ax.set_ylabel('Mean emotional value' if lang == 'en' else '平均情感值', fontsize=13)
        ax.grid(alpha=.25)
        ax.set_axisbelow(True)
        ax.set_ylim(-1.3, 4.2)
        plt.tight_layout()
        fig.savefig(f'{out}/图6_王朝情感曲线_{lang.upper()}.png', dpi=300)
        plt.close(fig)

        # 图7、图8：意象轨迹拆成两张独立图（词表在 config.py 里改）
        draw_trajectory(config.TRAJ_POS_WORDS, 7,
                        'Emotional trajectories of positive-leaning imageries '
                        'across the four Tang periods',
                        '偏正向意象的四期情感轨迹（各期独立计算）', lang)
        draw_trajectory(config.TRAJ_NEG_WORDS, 8,
                        'Emotional trajectories of negative-leaning imageries '
                        'across the four Tang periods',
                        '偏负向意象的四期情感轨迹（各期独立计算）', lang)

    print(f'\n全部结果已保存到: {out}')


if __name__ == '__main__':
    main()
