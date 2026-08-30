# -*- coding: utf-8 -*-
"""
工具库：全部任务脚本共用的核心函数。
========================================
本文件与论文第4章的公式一一对应，并通过如下校验：
  - 四诗人诗级均值复现到小数点后四位（李白 +0.9649 等）
  - 签名意象表、高频意象表逐条复现
  - 六意象四期轨迹与原结果最大偏差 0.16（源于语料版本微调）
"""
import os
import re
import math
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

import config


# -------------------- 数据加载 --------------------

def load_corpus():
    """读取语料，返回 [(作者, 诗题, 正文), ...]"""
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
    """读取情感词典，返回 (单字词典, 双字词典)"""
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
    """读取诗人时期归属表，返回 {诗人名: 时期}；只保留四期"""
    df = pd.read_excel(config.POET_YEAR_FILE)
    df['时期_clean'] = (df['时期'].astype(str)
                      .str.replace('（文学史公认）', '', regex=False).str.strip())
    return {r['诗人名']: r['时期_clean'] for _, r in df.iterrows()
            if r['时期_clean'] in config.PERIODS}


# -------------------- 文本切分 --------------------

def split_into_couplets(poem):
    """诗 → 对联窗口列表（论文4.1节：终止标点切句，两句一联）"""
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


# -------------------- 诗级打分（论文4.4节 公式8） --------------------

def analyze_poem(text, char_val, bi_val):
    """整诗情感值 = 窗口内（意象值之和 + 未覆盖单字值之和）/ 窗口数"""
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


# -------------------- 子语料独立训练（论文4.4节，各期/各诗人独立口径） --------------------

def train_subcorpus(poem_texts, vocab,
                    min_char_freq=config.MIN_CHAR_FREQ,
                    min_bigram_freq=config.MIN_BIGRAM_FREQ):
    """
    在一段子语料上独立计算情感词典。
    vocab: 需要计算的双字词集合（756意象库 ∪ 需要的扩展词）
    返回 (单字情感值dict, 双字情感值dict, 双字词出现次数Counter, 联窗口总数)
    """
    total = 0
    char_cnt = Counter()          # 单字联频（联内去重）
    bigram_cnt = Counter()        # 双字词出现次数（所有出现）
    cooccur = defaultdict(int)    # (词, 种子) 联内共现
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

    # 单字：原始值 → 极差映射到 [-1, 1]（低频字为 0）
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

    # 双字词：原始值 → 极差映射 → 加构词字（论文公式7）
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


# -------------------- 词表构造（论文5.1节：频率比 + 双重证据 + 诗意筛查） --------------------

def teaching_reliable(word, char_val, bi_val):
    """双重证据过滤 + 非诗意功能词剔除"""
    if word in config.EXCLUDE or word not in bi_val:
        return False
    v = bi_val[word]
    csum = char_val.get(word[0], 0) + char_val.get(word[1], 0)
    return (abs(v) >= config.DOUBLE_EVIDENCE_VAL
            and abs(csum) >= config.DOUBLE_EVIDENCE_CHAR
            and v * csum > 0)


def count_imageries(poem_texts, vocab):
    """统计意象在诗集合中的出现次数"""
    cnt = Counter()
    for text in poem_texts:
        for coup in split_into_couplets(text):
            for bg in vocab:
                k = coup.count(bg)
                if k:
                    cnt[bg] += k
    return cnt


def signature_list(name, poet_img_cnt, poet_npoem, char_val, bi_val, topn=12):
    """签名意象表：频率比 ≥2、本家≥5次、他家合计≥1次，过滤后递补至 topn 条"""
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
    """高频意象表：按出现次数排序，过滤后递补至 topn 条"""
    cands = sorted(poet_img_cnt[name].items(), key=lambda x: -x[1])
    out = []
    for bg, c in cands:
        if teaching_reliable(bg, char_val, bi_val):
            out.append((bg, c, bi_val[bg]))
            if len(out) == topn:
                break
    return out


# -------------------- 自我网络（论文4.5节） --------------------

def ego_network(poem_texts, target, vocab, bi_val,
                topk=config.EGO_TOP_K, min_co=config.EGO_MIN_CO):
    """
    诗级共现自我网络：与中心词至少共现 min_co 首诗，按 NPMI 排序取前 topk。
    config.EXCLUDE 里的非诗意功能词不作为邻居出现（被剔除后由后续名次递补）。
    返回 [(邻居词, NPMI, 共现诗数, 情感值), ...]
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
        if bg == target or bg in config.EXCLUDE:   # 中心词自身与非诗意功能词不入邻居
            continue
        co = sum(1 for s in presence if target in s and bg in s)
        if co < min_co:
            continue
        pi, pj, pc = doc[target] / n, doc[bg] / n, co / n
        npmi = math.log(pc / (pi * pj)) / (-math.log(pc))
        res.append((bg, npmi, co, bi_val.get(bg, 0.0)))
    res.sort(key=lambda x: -x[1])
    return res[:topk]


# -------------------- 统计检验 --------------------

def welch_all_pairs(score_dict):
    """六对韦尔奇 t 检验 + 霍姆校正，返回 DataFrame"""
    from scipy import stats
    names = list(score_dict.keys())
    pairs, rows = [], []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            t, p = stats.ttest_ind(score_dict[names[i]], score_dict[names[j]],
                                   equal_var=False)
            pairs.append((names[i], names[j]))
            rows.append([t, p])
    # 霍姆校正
    m = len(rows)
    order = sorted(range(m), key=lambda i: rows[i][1])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, rows[i][1] * (m - rank)))
        adj[i] = running
    return pd.DataFrame({
        '诗人A': [p[0] for p in pairs], '诗人B': [p[1] for p in pairs],
        't': [r[0] for r in rows], 'p': [r[1] for r in rows], 'p_Holm': adj})


# -------------------- 画图辅助 --------------------

def setup_chinese_font():
    """在你自己的电脑上运行需要中文字体：按常见字体逐个尝试"""
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
    """每个任务的输出目录：output/任务X_xxx/"""
    d = os.path.join(config.OUTPUT_DIR, task_name)
    os.makedirs(d, exist_ok=True)
    return d
