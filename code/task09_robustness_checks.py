# -*- coding: utf-8 -*-
"""
Task 9: Robustness checks (paper Sections 4.4 and 4.6)
======================================================
A. Threshold sensitivity of the double-evidence filter: vary the two cut-offs
   within ±0.05–0.10 and report the size of the passing set and its Jaccard
   overlap with the default set (336 imageries).
   Data source: the released dictionaries under input/; no corpus pass needed.
B. Seed-composition sensitivity: recompute the entire pipeline under twelve
   resampled seed sets (35 of 50 per polarity in each) and check three
   ranking-level conclusions:
   1) textbook-canon mean < full-corpus mean
   2) period means Early > High > Mid (the Mid–Late gap is reported separately)
   3) Li Bai ranks top among the four poets
   Note: part B traverses the corpus once (about 40 seconds); each
   configuration then only rebuilds the dictionaries and re-scores the poems.
"""
import math, random, re, os
from collections import Counter, defaultdict
import pandas as pd
import config

# ---------- A. Threshold sensitivity ----------
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
    lines = [f'Default cut-offs |v|>={config.DOUBLE_EVIDENCE_VAL} and |c1+c2|>={config.DOUBLE_EVIDENCE_CHAR}: {len(base)} imageries pass', '',
             'val_th\tchar_th\tpassing\tJaccard vs default']
    for vth in [0.20, 0.25, 0.35, 0.40]:
        for cth in [0.10, 0.15, 0.25, 0.30]:
            s = pass_set(bi_val, char_val, vth, cth)
            j = len(s & base) / len(s | base)
            lines.append(f'{vth:.2f}\t{cth:.2f}\t{len(s)}\t{j:.3f}')
    with open(f'{outdir}/threshold_sensitivity.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines))

# ---------- B. Seed sensitivity ----------
def run_seed_sensitivity(outdir, n_config=12, n_draw=35):
    from utils import load_corpus, load_period_map, split_into_couplets
    poems = load_corpus()
    period_map = load_period_map()
    # canon poem keys: (author, corpus title) from the released 108-poem scoring
    # table produced by Task 5 (data/textbook_canon_108_scoring.csv)
    canon_path = os.path.join(os.path.dirname(config.BASE_DIR), 'data', 'textbook_canon_108_scoring.csv')
    canon_csv = pd.read_csv(canon_path)
    canon_keys = set(zip(canon_csv['author'], canon_csv['corpus_title']))

    _, _, bi_val = load_dicts_full()
    VOCAB = set(bi_val.keys())
    POS, NEG = sorted(config.POS_SEEDS), sorted(config.NEG_SEEDS)
    ALL = set(POS) | set(NEG)

    # single corpus pass: counts + compact per-poem records
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

    lines = ['Config\tEarly>High>Mid\tMid>Late\tCanon<Corpus\tLiBai_top']
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
              f'Early > High > Mid holds: {n_order}/{n_config}',
              f'Mid > Late holds: {n_ml}/{n_config} (this gap is non-significant by default, Tukey p = 0.054)',
              f'Canon < Corpus holds: {n_canon}/{n_config}',
              f'Li Bai top-ranked: {n_libai}/{n_config}']
    with open(f'{outdir}/seed_sensitivity.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines[-4:]))

if __name__ == '__main__':
    from utils import task_outdir
    outdir = task_outdir('task09_robustness')
    os.makedirs(outdir, exist_ok=True)
    print('=== A. Double-evidence threshold sensitivity ===')
    run_threshold_sensitivity(outdir)
    print('\n=== B. Seed-composition sensitivity (one corpus pass, about 1 minute) ===')
    run_seed_sensitivity(outdir)
