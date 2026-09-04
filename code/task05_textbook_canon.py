# -*- coding: utf-8 -*-
"""
Task 5: Textbook-canon evidence package
=======================================
What it does:
  1. Loads input/textbook_items_110.csv (Tang-poem items in the centrally
     compiled textbooks, with title corrections and signature strings);
  2. Matches items to the corpus by author + title (title variants in the
     transmitted text resolved by content signatures);
  3. Scores each poem and outputs the canon-level statistics, distributions
     by author and by period, the canon's high-frequency imageries (after the
     function-word screen), and the canon-vs-corpus dumbbell figure (paper
     Figure 9).

Outputs (output/task05_textbook_canon/):
  - canon_perpoem_scores.csv   data behind paper Section 7.1 and Appendix B
  - canon_stats.txt            descriptive statistics overall / by author /
                               by period (the numbers in Section 7.2)
  - canon_highfreq_imageries.csv
  - figure9_canon_vs_corpus_EN/CN.png

Run: python task05_textbook_canon.py
"""
from collections import defaultdict, Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config
import utils


def norm_title(t):
    t = t.replace('节选', '').replace('并序', '').strip()
    return t


def main():
    utils.setup_chinese_font()
    out = utils.task_outdir('task05_textbook_canon')

    poems = utils.load_corpus()
    char_val, bi_val = utils.load_dicts()
    vocab = set(bi_val.keys())
    name2period = utils.load_period_map()
    # minor poets absent from the year table are added per literary-history
    # consensus (the rule set's first priority)
    name2period.update({'王之涣': '盛唐', '高适': '盛唐', '张志和': '中唐',
                        '胡令能': '中唐', '张若虚': '初唐'})

    corpus_by_author = defaultdict(list)
    for a, ti, txt in poems:
        corpus_by_author[a].append((ti, txt))

    canon = pd.read_csv(config.CANON_FILE).fillna('')
    found, missing = [], []
    for _, r in canon.iterrows():
        title, author = r['教材题名'], r['作者']
        sig_, fix, alias = r['签名串'], r['修正题名'], r['作者别名']
        cands = corpus_by_author.get(alias or author, [])
        nt = norm_title(fix or title)
        hits = [(ti, txt) for ti, txt in cands if norm_title(ti) == nt or nt in norm_title(ti)]
        if sig_ and hits:
            h2 = [h for h in hits if sig_ in h[1]]
            if h2:
                hits = h2
        if hits:
            found.append({'教材题名': title, '作者': author,
                          '语料题名': hits[0][0], '正文': hits[0][1]})
        else:
            missing.append((title, author))

    print(f'Item matching: {len(found)} matched, {len(missing)} without corpus counterpart: {missing}')

    rows = []
    for item in found:
        v = utils.analyze_poem(item['正文'], char_val, bi_val)
        rows.append({'textbook_title': item['教材题名'], 'author': item['作者'],
                     'corpus_title': item['语料题名'], 'value': round(v, 4),
                     'period': name2period.get(item['作者'], '')})
    cdf = pd.DataFrame(rows)
    cdf.to_csv(f'{out}/canon_perpoem_scores.csv', index=False, encoding='utf-8-sig')

    # statistics
    all_scores = np.array([v for v in (utils.analyze_poem(t, char_val, bi_val)
                                       for _, _, t in poems) if v is not None])
    with open(f'{out}/canon_stats.txt', 'w', encoding='utf-8') as f:
        f.write(f'Canon: n={len(cdf)}, mean={cdf["value"].mean():+.4f}, '
                f'positive%={100 * (cdf["value"] > 0).mean():.1f}\n')
        f.write(f'Full corpus: n={len(all_scores)}, mean={all_scores.mean():+.4f}, '
                f'positive%={100 * (all_scores > 0).mean():.1f}\n\nBy author:\n')
        f.write(cdf.groupby('author')['value'].agg(['count', 'mean'])
                .sort_values('count', ascending=False).to_string())
        f.write('\n\nBy period:\n')
        f.write(cdf.groupby('period')['value'].agg(['count', 'mean']).to_string())
    print(f'Canon: n={len(cdf)}, mean={cdf["value"].mean():+.3f}, '
          f'positive%={100 * (cdf["value"] > 0).mean():.1f}')
    print(f'Full corpus: mean={all_scores.mean():+.3f}, positive%={100 * (all_scores > 0).mean():.1f}')

    # canon high-frequency imageries (after the screen)
    canon_cnt = Counter()
    for item in found:
        for coup in utils.split_into_couplets(item['正文']):
            for bg in vocab:
                if bg in config.EXCLUDE:
                    continue
                k = coup.count(bg)
                if k:
                    canon_cnt[bg] += k
    top = [(bg, c, bi_val[bg]) for bg, c in canon_cnt.most_common(20) if c >= 4]
    pd.DataFrame([[bg, config.TRANS.get(bg, ''), c, f'{v:+.4f}'] for bg, c, v in top],
                 columns=['Imagery', 'English', 'Occurrences', 'Value']
                 ).to_csv(f'{out}/canon_highfreq_imageries.csv', index=False, encoding='utf-8-sig')
    print('Canon high-frequency imageries (screened):', ', '.join(f'{bg}({c})' for bg, c, _ in top))

    # Figure 9: dumbbell (canon vs complete works, four poets)
    poet_full_mean = {}
    for n in config.POETS:
        vals = [v for v in (utils.analyze_poem(txt, char_val, bi_val)
                            for ti, txt in corpus_by_author[n]) if v is not None]
        poet_full_mean[n] = np.mean(vals)
    canon_m = [cdf[cdf['author'] == n]['value'].mean() for n in config.POETS]
    canon_n = [len(cdf[cdf['author'] == n]) for n in config.POETS]
    full_m = [poet_full_mean[n] for n in config.POETS]

    for lang in ['en', 'cn']:
        fig, ax = plt.subplots(figsize=(10, 5.5))
        y = list(range(4))[::-1]
        for yi, cm, fm in zip(y, canon_m, full_m):
            ax.plot([cm, fm], [yi, yi], color='#999', lw=2.5, zorder=1)
        ax.scatter(canon_m, y, s=180, color='#d4574c', zorder=3,
                   label='Textbook canon poems' if lang == 'en' else '教材选诗')
        ax.scatter(full_m, y, s=180, color='#2e5d8a', zorder=3,
                   label='Complete works' if lang == 'en' else '全集')
        for yi, cm, fm in zip(y, canon_m, full_m):
            ax.annotate(f'{cm:+.2f}', (cm - 0.04, yi + 0.18), ha='right', fontsize=11,
                        color='#d4574c', fontweight='bold')
            ax.annotate(f'{fm:+.2f}', (fm + 0.04, yi + 0.18), ha='left', fontsize=11,
                        color='#2e5d8a', fontweight='bold')
        ax.axvline(0, ls='--', color='gray', lw=1)
        ylabels = [f'{config.POET_EN[n]} (canon n={cn})' if lang == 'en'
                   else f'{n}（教材{cn}首）' for n, cn in zip(config.POETS, canon_n)]
        ax.set_yticks(y)
        ax.set_yticklabels(ylabels, fontsize=12)
        ax.set_xlabel('Mean emotional value' if lang == 'en' else '平均情感值', fontsize=13)
        ax.legend(fontsize=11, loc='lower left')
        ax.grid(axis='x', alpha=.25)
        ax.set_axisbelow(True)
        plt.tight_layout()
        fig.savefig(f'{out}/figure9_canon_vs_corpus_{lang.upper()}.png', dpi=300)
        plt.close(fig)

    print(f'\nAll results saved to: {out}')


if __name__ == '__main__':
    main()
