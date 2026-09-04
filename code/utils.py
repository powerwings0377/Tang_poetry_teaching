# -*- coding: utf-8 -*-
"""
Utility library: core functions shared by all task scripts.
=====================================================================
This file corresponds one-to-one to the formulas in Section 4 of the
paper, and is verified by the following checks:
  - poem-level means of the four poets reproduce to four decimals
    (Li Bai +0.9649, etc.)
  - signature-imagery and high-frequency lists reproduce item by item
  - six-imagery four-period trajectories deviate by at most 0.16 from
    the original results (owing to a minor corpus-version adjustment)
"""
import os
import re
import math
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

import config


# -------------------- Data loading --------------------

def load_corpus():
    """Load the corpus; returns [(author, title, text), ...]"""
    poems = []
    with open(config.CORPUS_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.strip():
                continue
            parts = line.split('#')
            if len(parts) >= 3:
                poems.append((parts[0], parts[1], ''.join(parts[2:])))
    return poems


def load_dicts():
    """Load the emotional-value dictionaries; returns (char dict, bigram dict)"""
    char_val = {}
    with open(config.CHAR_DICT_FILE, encoding='utf-8') as f:
        next(f)
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) >= 2:
                try:
                    char_val[p[0]] = float(p[1])
                except ValueError:
                    pass
    bi_val = {}
    with open(config.BIGRAM_DICT_FILE, encoding='utf-8') as f:
        next(f)
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) >= 2:
                try:
                    bi_val[p[0]] = float(p[1])
                except ValueError:
                    pass
    return char_val, bi_val


def load_period_map():
    """Load the poet-period assignment table; returns {poet: period}; keeps only the four periods"""
    df = pd.read_excel(config.POET_YEAR_FILE)
    df['时期_clean'] = (df['时期'].astype(str)
                      .str.replace('（文学史公认）', '', regex=False).str.strip())
    return {r['诗人名']: r['时期_clean'] for _, r in df.iterrows()
            if r['时期_clean'] in config.PERIODS}


# -------------------- Text segmentation --------------------

def split_into_couplets(poem):
    """Poem -> list of couplet windows (paper Section 4.1: split at terminal punctuation, two lines per window)"""
    sentences = re.split(r'[。！？]', poem)
    clean = []
    for s in sentences:
        c = re.sub(r'[，、；：""\'\'（）【】《》\s]', '', s.strip())
        if c:
            clean.append(c)
    couplets = []
    for i in range(0, len(clean), 2):
        couplets.append(clean[i] + clean[i + 1] if i + 1 < len(clean) else clean[i])
    return [c for c in couplets if c]


# -------------------- Poem-level scoring (paper Section 4.4) --------------------

def analyze_poem(text, char_val, bi_val):
    """Poem emotional value = (sum of imagery values + uncovered character values) / number of windows"""
    couplets = split_into_couplets(text)
    if not couplets:
        return None
    total = 0.0
    for coup in couplets:
        covered = set()
        for bg, val in bi_val.items():
            start = 0
            while True:
                idx = coup.find(bg, start)
                if idx == -1:
                    break
                total += val
                covered.add(idx)
                covered.add(idx + 1)
                start = idx + 1
        for i, ch in enumerate(coup):
            if i not in covered:
                total += char_val.get(ch, 0.0)
    return total / len(couplets)


# -------------------- Independent subcorpus training (paper Section 4.4; per-period / per-poet) --------------------

def train_subcorpus(poem_texts, vocab,
                    min_char_freq=config.MIN_CHAR_FREQ,
                    min_bigram_freq=config.MIN_BIGRAM_FREQ):
    """
    Compute the emotional dictionaries independently on a subcorpus.
    vocab: the set of bigrams to score (the 756-imagery inventory plus any extension words)
    Returns (char values dict, bigram values dict, bigram occurrence Counter, total window count)
    """
    total = 0
    char_cnt = Counter()          # character window frequency (deduplicated within a window)
    bigram_cnt = Counter()        # bigram occurrences (all occurrences)
    cooccur = defaultdict(int)    # (word, seed) in-window co-occurrence
    for text in poem_texts:
        for coup in split_into_couplets(text):
            total += 1
            chars = set(coup)
            for ch in chars:
                char_cnt[ch] += 1
            bg_here = {bg: coup.count(bg) for bg in vocab if bg in coup}
            for bg, k in bg_here.items():
                bigram_cnt[bg] += k
            seeds_here = chars & config.ALL_SEEDS
            for seed in seeds_here:
                for ch in chars:
                    cooccur[(ch, seed)] += 1
            for bg in bg_here:
                for seed in seeds_here:
                    cooccur[(bg, seed)] += 1

    def npmi(word, seed):
        cw = char_cnt.get(word, 0) if len(word) == 1 else bigram_cnt.get(word, 0)
        cs = char_cnt.get(seed, 0)
        cb = cooccur.get((word, seed), 0)
        if cw == 0 or cs == 0 or cb == 0:
            return 0.0
        pw, ps, pb = cw / total, cs / total, cb / total
        try:
            v = math.log(pb / (pw * ps)) / (-math.log(pb))
            return max(-1.0, min(1.0, v))
        except (ValueError, ZeroDivisionError):
            return 0.0

    def avg_seeds(word, seeds):
        vals = [v for v in (npmi(word, s) for s in seeds) if v != 0]
        return sum(vals) / len(vals) if vals else 0.0

    # Characters: raw value -> min-max mapped to [-1, 1] (low-frequency characters get 0)
    raw_char = {}
    for ch, freq in char_cnt.items():
        if freq < min_char_freq:
            raw_char[ch] = 0.0
        else:
            raw_char[ch] = (avg_seeds(ch, config.POS_SEEDS)
                            - avg_seeds(ch, config.NEG_SEEDS)) / 2.0
    valid_chars = [c for c, f in char_cnt.items() if f >= min_char_freq]
    raws = [raw_char[c] for c in valid_chars]
    rmin, rmax = min(raws), max(raws)
    char_emo = {}
    for ch, raw in raw_char.items():
        if char_cnt[ch] < min_char_freq or rmax == rmin:
            char_emo[ch] = 0.0
        else:
            char_emo[ch] = -1.0 + 2.0 * (raw - rmin) / (rmax - rmin)

    # Bigrams: raw value -> min-max mapping -> plus constituent characters (paper formula)
    raw_bi = {}
    for bg in vocab:
        if bigram_cnt.get(bg, 0) < min_bigram_freq:
            raw_bi[bg] = 0.0
        else:
            raw_bi[bg] = (avg_seeds(bg, config.POS_SEEDS)
                          - avg_seeds(bg, config.NEG_SEEDS)) / 2.0
    valid_bi = [bg for bg in vocab if bigram_cnt.get(bg, 0) >= min_bigram_freq]
    braws = [raw_bi[bg] for bg in valid_bi]
    bmin, bmax = min(braws), max(braws)
    bi_emo = {}
    for bg in vocab:
        if bigram_cnt.get(bg, 0) < min_bigram_freq or bmax == bmin:
            base = 0.0
        else:
            base = -1.0 + 2.0 * (raw_bi[bg] - bmin) / (bmax - bmin)
        bi_emo[bg] = base + char_emo.get(bg[0], 0.0) + char_emo.get(bg[1], 0.0)

    return char_emo, bi_emo, bigram_cnt, total


# -------------------- List construction (paper Section 5.1: frequency ratio + double evidence + poeticity screen) --------------------

def teaching_reliable(word, char_val, bi_val):
    """Double-evidence filter + removal of non-poetic function words"""
    if word in config.EXCLUDE or word not in bi_val:
        return False
    v = bi_val[word]
    csum = char_val.get(word[0], 0) + char_val.get(word[1], 0)
    return (abs(v) >= config.DOUBLE_EVIDENCE_VAL
            and abs(csum) >= config.DOUBLE_EVIDENCE_CHAR
            and v * csum > 0)


def count_imageries(poem_texts, vocab):
    """Count imagery occurrences in a poem collection"""
    cnt = Counter()
    for text in poem_texts:
        for coup in split_into_couplets(text):
            for bg in vocab:
                k = coup.count(bg)
                if k:
                    cnt[bg] += k
    return cnt


def signature_list(name, poet_img_cnt, poet_npoem, char_val, bi_val, topn=12):
    """Signature-imagery list: frequency ratio >= 2, >= 5 occurrences in the poet, >= 1 in the others combined; filtered entries are replaced by promotion until topn remain"""
    cands = []
    for bg, c in poet_img_cnt[name].items():
        if c < 5:
            continue
        others = sum(poet_img_cnt[o][bg] for o in poet_img_cnt if o != name)
        if others == 0:
            continue
        others_n = sum(poet_npoem[o] for o in poet_npoem if o != name)
        ratio = (c / poet_npoem[name]) / (others / others_n)
        if ratio >= 2:
            cands.append((bg, c, ratio))
    cands.sort(key=lambda x: -x[2])
    out = []
    for bg, c, r in cands:
        if teaching_reliable(bg, char_val, bi_val):
            out.append((bg, c, r, bi_val[bg]))
            if len(out) == topn:
                break
    return out


def highfreq_list(name, poet_img_cnt, char_val, bi_val, topn=12):
    """High-frequency imagery list: ranked by raw occurrence counts; filtered entries are replaced by promotion until topn remain"""
    cands = sorted(poet_img_cnt[name].items(), key=lambda x: -x[1])
    out = []
    for bg, c in cands:
        if teaching_reliable(bg, char_val, bi_val):
            out.append((bg, c, bi_val[bg]))
            if len(out) == topn:
                break
    return out


# -------------------- Ego networks (paper Section 4.5) --------------------

def ego_network(poem_texts, target, vocab, bi_val,
                topk=config.EGO_TOP_K, min_co=config.EGO_MIN_CO):
    """
    Poem-level co-occurrence ego network: neighbours share at least min_co poems with the centre word, ranked by NPMI, top topk kept.
    Non-poetic function words in config.EXCLUDE never appear as neighbours (removed and replaced by promotion).
    Returns [(neighbour, NPMI, shared poems, emotional value), ...]
    """
    presence = []
    for text in poem_texts:
        s = set()
        for coup in split_into_couplets(text):
            for bg in vocab:
                if bg in coup:
                    s.add(bg)
        presence.append(s)
    n = len(presence)
    doc = Counter()
    for s in presence:
        for bg in s:
            doc[bg] += 1
    res = []
    for bg in doc:
        if bg == target or bg in config.EXCLUDE:   # the centre itself and non-poetic function words are never neighbours
            continue
        co = sum(1 for s in presence if target in s and bg in s)
        if co < min_co:
            continue
        pi, pj, pc = doc[target] / n, doc[bg] / n, co / n
        npmi = math.log(pc / (pi * pj)) / (-math.log(pc))
        res.append((bg, npmi, co, bi_val.get(bg, 0.0)))
    res.sort(key=lambda x: -x[1])
    return res[:topk]


# -------------------- Statistical tests --------------------

def welch_all_pairs(score_dict):
    """Six pairwise Welch t-tests with Holm correction; returns a DataFrame"""
    from scipy import stats
    names = list(score_dict.keys())
    pairs, rows = [], []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            t, p = stats.ttest_ind(score_dict[names[i]], score_dict[names[j]],
                                   equal_var=False)
            pairs.append((names[i], names[j]))
            rows.append([t, p])
    # Holm correction
    m = len(rows)
    order = sorted(range(m), key=lambda i: rows[i][1])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, rows[i][1] * (m - rank)))
        adj[i] = running
    return pd.DataFrame({
        'Poet_A': [p[0] for p in pairs], 'Poet_B': [p[1] for p in pairs],
        't': [r[0] for r in rows], 'p': [r[1] for r in rows], 'p_Holm': adj})


# -------------------- Plotting helpers --------------------

def setup_chinese_font():
    """A Chinese font is required on your own machine: try common fonts in turn"""
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    for f in ['Microsoft YaHei', 'SimHei', 'PingFang SC',
              'Noto Sans CJK SC', 'WenQuanYi Zen Hei']:
        try:
            font_manager.findfont(f, fallback_to_default=False)
            plt.rcParams['font.sans-serif'] = [f]
            break
        except Exception:
            continue
    plt.rcParams['axes.unicode_minus'] = False


def task_outdir(task_name):
    """Per-task output directory: output/<task>/"""
    d = os.path.join(config.OUTPUT_DIR, task_name)
    os.makedirs(d, exist_ok=True)
    return d
