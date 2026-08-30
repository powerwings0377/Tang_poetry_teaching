# -*- coding: utf-8 -*-
"""
任务五：教材正典证据包
================================
做什么：
  1. 读取 input/教材篇目_110条.csv（统编教材唐诗条目，含题名修正与签名串）；
  2. 按作者+题名匹配到语料正文（传世题名差异用签名串核对）；
  3. 每首打分，输出正典整体统计、按作者/时期的分布、正典高频意象
     （经非诗意功能词筛查）、教材对全集哑铃图（图8）。

输出（output/任务五/）：
  - 教材正典_逐首打分.csv     论文7.1节与附录B的数据来源
  - 教材正典_统计.txt         整体/按作者/按时期的描述统计（7.2节数字来源）
  - 教材正典_高频意象.csv     筛查后的正典高频意象
  - 图8_教材对全集_EN/CN.png

运行：python 任务五_教材正典证据包.py
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
    out = utils.task_outdir('任务五_教材正典证据包')

    poems = utils.load_corpus()
    char_val, bi_val = utils.load_dicts()
    vocab = set(bi_val.keys())
    name2period = utils.load_period_map()
    # 年份表外的小诗人，按文学史共识补（规则第一优先级）
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

    print(f'篇目匹配: 成功 {len(found)} 首，语料中无对应 {len(missing)} 首: {missing}')

    rows = []
    for item in found:
        v = utils.analyze_poem(item['正文'], char_val, bi_val)
        rows.append({'教材题名': item['教材题名'], '作者': item['作者'],
                     '语料题名': item['语料题名'], '情感值': round(v, 4),
                     '时期': name2period.get(item['作者'], '')})
    cdf = pd.DataFrame(rows)
    cdf.to_csv(f'{out}/教材正典_逐首打分.csv', index=False, encoding='utf-8-sig')

    # 统计
    all_scores = np.array([v for v in (utils.analyze_poem(t, char_val, bi_val)
                                       for _, _, t in poems) if v is not None])
    with open(f'{out}/教材正典_统计.txt', 'w', encoding='utf-8') as f:
        f.write(f'正典: n={len(cdf)}, 均值={cdf["情感值"].mean():+.4f}, '
                f'积极%={100 * (cdf["情感值"] > 0).mean():.1f}\n')
        f.write(f'全语料: n={len(all_scores)}, 均值={all_scores.mean():+.4f}, '
                f'积极%={100 * (all_scores > 0).mean():.1f}\n\n按作者:\n')
        f.write(cdf.groupby('作者')['情感值'].agg(['count', 'mean'])
                .sort_values('count', ascending=False).to_string())
        f.write('\n\n按时期:\n')
        f.write(cdf.groupby('时期')['情感值'].agg(['count', 'mean']).to_string())
    print(f'正典: n={len(cdf)}, 均值={cdf["情感值"].mean():+.3f}, '
          f'积极%={100 * (cdf["情感值"] > 0).mean():.1f}')
    print(f'全语料: 均值={all_scores.mean():+.3f}, 积极%={100 * (all_scores > 0).mean():.1f}')

    # 正典高频意象（筛查后）
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
                 columns=['意象', '英文', '出现次数', '情感值']
                 ).to_csv(f'{out}/教材正典_高频意象.csv', index=False, encoding='utf-8-sig')
    print('正典高频意象（筛查后）:', ', '.join(f'{bg}({c})' for bg, c, _ in top))

    # 图8：哑铃图（四位诗人的正典 vs 全集）
    poet_full_mean = {}
    for n in config.POETS:
        vals = [v for v in (utils.analyze_poem(txt, char_val, bi_val)
                            for ti, txt in corpus_by_author[n]) if v is not None]
        poet_full_mean[n] = np.mean(vals)
    canon_m = [cdf[cdf['作者'] == n]['情感值'].mean() for n in config.POETS]
    canon_n = [len(cdf[cdf['作者'] == n]) for n in config.POETS]
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
        fig.savefig(f'{out}/图8_教材对全集_{lang.upper()}.png', dpi=300)
        plt.close(fig)

    print(f'\n全部结果已保存到: {out}')


if __name__ == '__main__':
    main()
