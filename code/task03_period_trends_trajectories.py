# -*- coding: utf-8 -*-
"""
Task 3: Period trends and imagery trajectories
==============================================
What it does:
  1. Dynasty-level emotional curve (paper Figure 7): period means, ANOVA,
     linear trend, Tukey pairwise comparisons. Palette switches in config.py
     (FIG6_PALETTE: 'classic' / 'warm' / 'forest');
  2. Imagery trajectories as two separate figures: positive-leaning group
     (config.TRAJ_POS_WORDS) and negative-leaning group (config.TRAJ_NEG_WORDS).
     Each period subcorpus is retrained independently (paper Section 4.4).
     To change the tracked words, edit the two lists in config.py and re-run.
     Hollow markers = fewer than 10 occurrences in that period, where the value
     rests on constituent characters alone.

Outputs (output/task03_period_trends/):
  - dynasty_curve_stats.txt     (per-period n / mean / sd / positive and negative
                                 shares + test results)
  - trajectory_values.csv       (value and occurrence count per word x period)
  - figure7_dynasty_curve_EN/CN.png, figure8a/8b_trajectories_EN/CN.png
    (with PDF versions)

Run: python task03_period_trends_trajectories.py   (about 3-5 minutes;
      four independent trainings)
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
    out = utils.task_outdir('task03_period_trends')

    poems = utils.load_corpus()
    char_val, bi_val = utils.load_dicts()
    vocab = set(bi_val.keys()) | set(config.TRAJ_WORDS)
    name2period = utils.load_period_map()

    period_texts = {p: [t for a, _, t in poems if name2period.get(a) == p]
                    for p in config.PERIODS}

    # ---------- 1. Dynasty curve ----------
    print('=== 1. Dynasty-level emotional curve (paper Figure 7) ===')
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

    with open(f'{out}/dynasty_curve_stats.txt', 'w', encoding='utf-8') as f:
        f.write('Period\tPoems\tMean\tSD\tPositive%\tNegative%\n')
        for p in config.PERIODS:
            a = period_scores[p]
            f.write(f'{p}\t{len(a)}\t{a.mean():.4f}\t{a.std(ddof=1):.4f}\t'
                    f'{100 * (a > 0).mean():.1f}\t{100 * (a < 0).mean():.1f}\n')
            print(f'{p}: n={len(a)}  mean={a.mean():+.4f}  sd={a.std(ddof=1):.4f}')
        f.write(f'\nANOVA: F(3,{ns.sum() - 4}) = {F:.2f}, p = {p_anova:.2e}, eta2 = {eta2:.4f}\n')
        f.write(f'Linear trend: t = {t_lin:.2f}\n')
        f.write('\nTukey HSD pairwise comparisons:\n')
        for i in range(4):
            for j in range(i + 1, 4):
                f.write(f'  {config.PERIODS[i]} vs {config.PERIODS[j]}: '
                        f'diff={means[i] - means[j]:+.4f}, p={tukey.pvalue[i, j]:.4f}\n')
    print(f'ANOVA: F(3,{ns.sum() - 4})={F:.2f}, eta2={eta2:.4f}, linear trend t={t_lin:.2f}')
    print(f'Mid vs Late: p={tukey.pvalue[2, 3]:.4f}')

    # ---------- 2. Independent per-period training + trajectories ----------
    print('\n=== 2. Independent per-period training and trajectories ===')
    traj = {}
    for p in config.PERIODS:
        _, bi_emo, bigram_cnt, nwin = utils.train_subcorpus(period_texts[p], vocab)
        print(f'{p}: trained, windows={nwin}')
        for w in config.TRAJ_WORDS:
            traj.setdefault(w, {})[p] = (bi_emo.get(w, 0.0), bigram_cnt.get(w, 0))

    rows = []
    for w in config.TRAJ_WORDS:
        for p in config.PERIODS:
            v, c = traj[w][p]
            rows.append([w, config.TRANS.get(w, ''), p, round(v, 4), c,
                         'below10' if c < config.MIN_BIGRAM_FREQ else ''])
    pd.DataFrame(rows, columns=['Imagery', 'English', 'Period', 'Value', 'Occurrences', 'Below10_flag']
                 ).to_csv(f'{out}/trajectory_values.csv', index=False, encoding='utf-8-sig')

    # ---------- plotting ----------
    pal = config.PALETTES[config.FIG6_PALETTE]   # dynasty-curve palette (switch in config.py)

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
        """One trajectory figure: one line per word; the shaded band marks the post-rebellion periods"""
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
        fig.savefig(f'{out}/figure{fig_no}_trajectories_{lang.upper()}.png', dpi=300)
        fig.savefig(f'{out}/figure{fig_no}_trajectories_{lang.upper()}.pdf')
        plt.close(fig)

    for lang in ['en', 'cn']:
        # Figure 7: dynasty curve (palette switchable via FIG6_PALETTE in config.py)
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
        fig.savefig(f'{out}/figure7_dynasty_curve_{lang.upper()}.png', dpi=300)
        plt.close(fig)

        # trajectory figures: two separate plots (word lists live in config.py)
        draw_trajectory(config.TRAJ_POS_WORDS, '8a',
                        'Emotional trajectories of positive-leaning imageries '
                        'across the four Tang periods',
                        '偏正向意象的四期情感轨迹（各期独立计算）', lang)
        draw_trajectory(config.TRAJ_NEG_WORDS, '8b',
                        'Emotional trajectories of negative-leaning imageries '
                        'across the four Tang periods',
                        '偏负向意象的四期情感轨迹（各期独立计算）', lang)

    print(f'\nAll results saved to: {out}')


if __name__ == '__main__':
    main()
