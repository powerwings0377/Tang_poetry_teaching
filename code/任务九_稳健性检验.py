# -*- coding: utf-8 -*-
"""
任务九：稳健性检验（论文4.4与4.7节）
====================================
A. 双重证据阈值敏感性：在±0.05~0.10范围内变动两个阈值，
   统计通过意象数及其与默认集合（336个）的Jaccard重叠度。
   数据来源：input/ 下已发布的单字、双字情感值词典，无需重跑语料。
B. 种子构成敏感性：十二组重抽样种子集（正负各抽35/50）下重算整条流水线，
   检验三个排序级结论的稳定性：
   1) 教材正典均值 < 全集均值
   2) 时期均值 初唐 > 盛唐 > 中唐（晚唐差距小，单独报告）
   3) 李白居四诗人之首
   说明：B需要完整遍历语料一次（约40秒），之后每组配置只做字典重算与诗级打分。
"""
import math, random, re, os
from collections import Counter, defaultdict
import pandas as pd
import config

# ---------- A. 阈值敏感性 ----------
def load_dicts_full():
    char_val, char_freq = {}, {}
    with open(config.CHAR_DICT_FILE, encoding='utf-8') as f:
        next(f)
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) >= 4:
                char_val[p[0]] = float(p[1]); char_freq[p[0]] = int(p[3])
    bi_val = {}
    with open(config.BIGRAM_DICT_FILE, encoding='utf-8') as f:
        next(f)
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) >= 2:
                bi_val[p[0]] = float(p[1])
    return char_val, char_freq, bi_val

def pass_set(bi_val, char_val, vth, cth):
    out = set()
    for w, v in bi_val.items():
        cs = char_val.get(w[0], 0.0) + char_val.get(w[1], 0.0)
        if abs(v) >= vth and abs(cs) >= cth and v * cs > 0:
            out.add(w)
    return out

def run_threshold_sensitivity(outdir):
    char_val, _, bi_val = load_dicts_full()
    base = pass_set(bi_val, char_val, config.DOUBLE_EVIDENCE_VAL, config.DOUBLE_EVIDENCE_CHAR)
    lines = [f'默认阈值 |v|>={config.DOUBLE_EVIDENCE_VAL} 且 |c1+c2|>={config.DOUBLE_EVIDENCE_CHAR}：{len(base)} 个意象通过', '',
             'val_th\tchar_th\t通过数\t与默认集合的Jaccard']
    for vth in [0.20, 0.25, 0.35, 0.40]:
        for cth in [0.10, 0.15, 0.25, 0.30]:
            s = pass_set(bi_val, char_val, vth, cth)
            j = len(s & base) / len(s | base)
            lines.append(f'{vth:.2f}\t{cth:.2f}\t{len(s)}\t{j:.3f}')
    with open(f'{outdir}/阈值敏感性.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines))

# ---------- B. 种子敏感性 ----------
def run_seed_sensitivity(outdir, n_config=12, n_draw=35):
    from utils import load_corpus, load_period_map, split_into_couplets
    poems = load_corpus()
    period_map = load_period_map()
    # 正典诗键：使用已发布的108首打分表中的（作者, 语料题名）
    # 该表由任务五生成，放在代码包上一级目录；若不在，可先跑任务五生成
    canon_path = os.path.join(os.path.dirname(config.BASE_DIR), '教材正典108首_打分表.csv')
    canon_csv = pd.read_csv(canon_path)
    canon_keys = set(zip(canon_csv['作者'], canon_csv['语料题名']))

    _, _, bi_val = load_dicts_full()
    VOCAB = set(bi_val.keys())
    POS, NEG = sorted(config.POS_SEEDS), sorted(config.NEG_SEEDS)
    ALL = set(POS) | set(NEG)

    # 单次语料遍历：计数 + 每首诗的紧凑记录
    char_cnt, bigram_cnt, cooccur = Counter(), Counter(), defaultdict(int)
    total = 0
    poem_rec = []
    for author, title, text in poems:
        coups = [c for c in split_into_couplets(text) if c]
        img_occ, uncov = Counter(), Counter()
        for coup in coups:
            total += 1
            chars = set(coup)
            for ch in chars: char_cnt[ch] += 1
            covered, bg_here = set(), {}
            for bg in VOCAB:
                start = 0
                while True:
                    idx = coup.find(bg, start)
                    if idx == -1: break
                    img_occ[bg] += 1; bigram_cnt[bg] += 1
                    bg_here[bg] = True
                    covered.add(idx); covered.add(idx + 1)
                    start = idx + 1
            for i, ch in enumerate(coup):
                if i not in covered: uncov[ch] += 1
            for seed in chars & ALL:
                for ch in chars: cooccur[(ch, seed)] += 1
                for bg in bg_here: cooccur[(bg, seed)] += 1
        if coups:
            poem_rec.append((author, period_map.get(author),
                             (author, title) in canon_keys, len(coups), img_occ, uncov))

    def npmi(word, seed):
        cw = char_cnt.get(word, 0) if len(word) == 1 else bigram_cnt.get(word, 0)
        cs, cb = char_cnt.get(seed, 0), cooccur.get((word, seed), 0)
        if cw == 0 or cs == 0 or cb == 0: return 0.0
        pw, ps, pb = cw / total, cs / total, cb / total
        return max(-1.0, min(1.0, math.log(pb / (pw * ps)) / (-math.log(pb))))

    def build_dicts(pos_seeds, neg_seeds):
        def avg_seeds(word, seeds):
            vals = [v for v in (npmi(word, s) for s in seeds) if v != 0]
            return sum(vals) / len(vals) if vals else 0.0
        raw_char = {c: (0.0 if f < config.MIN_CHAR_FREQ
                        else (avg_seeds(c, pos_seeds) - avg_seeds(c, neg_seeds)) / 2.0)
                    for c, f in char_cnt.items()}
        raws = [v for c, v in raw_char.items() if char_cnt[c] >= config.MIN_CHAR_FREQ]
        rmin, rmax = min(raws), max(raws)
        char_emo = {c: (0.0 if char_cnt[c] < config.MIN_CHAR_FREQ or rmax == rmin
                        else -1.0 + 2.0 * (v - rmin) / (rmax - rmin))
                    for c, v in raw_char.items()}
        raw_bi = {bg: (0.0 if bigram_cnt.get(bg, 0) < config.MIN_BIGRAM_FREQ
                       else (avg_seeds(bg, pos_seeds) - avg_seeds(bg, neg_seeds)) / 2.0)
                  for bg in VOCAB}
        braws = [v for bg, v in raw_bi.items() if bigram_cnt.get(bg, 0) >= config.MIN_BIGRAM_FREQ]
        bmin, bmax = min(braws), max(braws)
        bi_emo = {}
        for bg, v in raw_bi.items():
            base = (0.0 if bigram_cnt.get(bg, 0) < config.MIN_BIGRAM_FREQ or bmax == bmin
                    else -1.0 + 2.0 * (v - bmin) / (bmax - bmin))
            bi_emo[bg] = base + char_emo.get(bg[0], 0.0) + char_emo.get(bg[1], 0.0)
        return char_emo, bi_emo

    def evaluate(char_emo, bi_emo):
        per_sum, per_n = defaultdict(float), Counter()
        canon_vals, all_vals = [], []
        poet_sum, poet_n = defaultdict(float), Counter()
        for author, period, is_canon, n_c, img_occ, uncov in poem_rec:
            v = (sum(bi_emo.get(b, 0.0) * k for b, k in img_occ.items())
                 + sum(char_emo.get(c, 0.0) * k for c, k in uncov.items())) / n_c
            all_vals.append(v)
            if is_canon: canon_vals.append(v)
            if period: per_sum[period] += v; per_n[period] += 1
            if author in config.POETS: poet_sum[author] += v; poet_n[author] += 1
        means = {p: per_sum[p] / per_n[p] for p in config.PERIODS}
        return means, sum(canon_vals) / len(canon_vals), sum(all_vals) / len(all_vals), \
               {a: poet_sum[a] / poet_n[a] for a in poet_sum}

    lines = ['配置\t初唐>盛唐>中唐\t中唐>晚唐\t正典<全集\t李白居首']
    n_order = n_ml = n_canon = n_libai = 0
    for k in range(n_config):
        rng = random.Random(1000 + k)
        ps = set(rng.sample(POS, n_draw)); ns = set(rng.sample(NEG, n_draw))
        ce, be = build_dicts(ps, ns)
        means, canon_m, full_m, pm = evaluate(ce, be)
        o1 = means['初唐'] > means['盛唐'] > means['中唐']
        o2 = means['中唐'] > means['晚唐']
        o3 = canon_m < full_m
        o4 = max(pm, key=pm.get) == '李白'
        n_order += o1; n_ml += o2; n_canon += o3; n_libai += o4
        lines.append(f'{k+1}\t{o1}\t{o2}\t{o3}\t{o4}')
    lines += ['',
              f'初唐>盛唐>中唐 成立：{n_order}/{n_config}',
              f'中唐>晚唐 成立：{n_ml}/{n_config}（该差距默认即不显著，Tukey p=0.054）',
              f'正典<全集 成立：{n_canon}/{n_config}',
              f'李白居首 成立：{n_libai}/{n_config}']
    with open(f'{outdir}/种子敏感性.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines[-4:]))

if __name__ == '__main__':
    outdir = config.task_outdir('任务九_稳健性检验') if hasattr(config, 'task_outdir') else 'output'
    import os; os.makedirs(outdir, exist_ok=True)
    print('=== A. 双重证据阈值敏感性 ===')
    run_threshold_sensitivity(outdir)
    print('\n=== B. 种子构成敏感性（需遍历语料一次，约1分钟）===')
    run_seed_sensitivity(outdir)
