# -*- coding: utf-8 -*-
"""
任务八：时期意象共现网络构建（初唐／盛唐／中唐／晚唐各一张）
================================
做什么：
  为唐代四个时期各建一张真实的意象共现网络，口径与任务七完全一致：
    - 节点：该期语料中出现不少于 NET_NODE_MIN 次的意象（初唐语料小也够用，
      四期统一用这个阈值）；config.EXCLUDE 里的功能词不作节点；
    - 边：两个意象在同一期同一首诗里共现至少 NET_CO_MIN 次，
      且诗级归一化点互信息 NPMI ≥ NET_NPMI_MIN；
    - 节点属性：频次、情感值；边属性：NPMI 权重。

输出（output/任务八/）——为写论文准备的完整数据：
  - 每期三个文件：{时期}_节点.csv、{时期}_边.csv、{时期}_网络.gexf
    （gexf 可直接拖进 Gephi）
  - 时期网络_结构指标.csv：每期的节点、边、平均度、密度、连通分量、
    最大连通占比、聚类系数、随机基线、平均路径、小世界系数、
    度分布指数、负向节点占比、负向意象出现占比、度中心前十、介数前十
  - 时期网络_摘要.txt：每期枢纽词与负向份额的速览（写对比段落直接用）
  - 图_四期意象共现网络_EN/CN.png：2×2 预览图

阈值都在本文件顶部，改完重跑即可。
运行：python 任务八_时期意象共现网络构建.py   （约2-3分钟）
"""
import math
import itertools
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

import config
import utils

# ---------- 可调阈值 ----------
NET_NODE_MIN = 10        # 节点最低出现次数（四期统一）
NET_NPMI_MIN = 0.3       # 边最低 NPMI
NET_CO_MIN = 2           # 边最低共现诗数
NET_LABEL_TOP = 8        # 每面板标注的高度数节点数
LAYOUT_SEED = 42         # 布局随机种子（固定后可复现同一张图）
CORE_TOP_N = 80          # 展示用核心节点数：完整网络太大看不清，
                         # 预览图只画度最高的前 80 个节点及其之间的边；
                         # 指标仍按完整网络计算，CORE_TOP_N 只影响展示


def period_presence(texts, vocab):
    """每首诗中出现的意象集合（剔除功能词）"""
    out = []
    for text in texts:
        s = set()
        for coup in utils.split_into_couplets(text):
            for bg in vocab:
                if bg not in config.EXCLUDE and bg in coup:
                    s.add(bg)
        out.append(s)
    return out


def fit_powerlaw_exponent(degrees, kmin=2):
    """对数-对数线性拟合估计度分布幂律指数（指示性，供参考）"""
    d = [k for k in degrees if k >= kmin]
    if len(d) < 8:
        return None
    cnt = Counter(degrees)
    xs = np.array(sorted([k for k in cnt if k >= kmin]), dtype=float)
    ys = np.array([np.log(cnt[int(k)] / len(degrees)) for k in xs])
    slope, _ = np.polyfit(np.log(xs), ys, 1)
    return round(-slope, 2)


def build_period_network(texts):
    pres = period_presence(texts, set(utils.load_dicts()[1].keys()))
    N = len(pres)
    doc = Counter()
    for s in pres:
        for bg in s:
            doc[bg] += 1
    nodes = [bg for bg, c in doc.items() if c >= NET_NODE_MIN]
    node_set = set(nodes)
    co = Counter()
    for s in pres:
        in_s = [bg for bg in s if bg in node_set]
        for a, b in itertools.combinations(sorted(in_s), 2):
            co[(a, b)] += 1
    edges = []
    for (a, b), c0 in co.items():
        if c0 < NET_CO_MIN:
            continue
        pa, pb, pc = doc[a] / N, doc[b] / N, c0 / N
        npmi = math.log(pc / (pa * pb)) / (-math.log(pc))
        if npmi >= NET_NPMI_MIN:
            edges.append((a, b, npmi, c0))
    return nodes, doc, edges


def main():
    utils.setup_chinese_font()
    out = utils.task_outdir('任务八_时期意象共现网络构建')
    poems = utils.load_corpus()
    _, bi_val = utils.load_dicts()
    name2period = utils.load_period_map()

    metric_rows = []
    summary = []
    graphs = {}
    for p in config.PERIODS:
        texts = [t for a, _, t in poems if name2period.get(a) == p]
        nodes, doc, edges = build_period_network(texts)
        G = nx.Graph()
        for bg in nodes:
            G.add_node(bg, frequency=doc[bg], valence=bi_val.get(bg, 0.0),
                       english=config.TRANS.get(bg, ''))
        for a, b, w, c0 in edges:
            G.add_edge(a, b, weight=w, co=c0)
        graphs[p] = G

        # 结构指标
        Nn, M = G.number_of_nodes(), G.number_of_edges()
        degrees = [d for _, d in G.degree()]
        avg_deg = 2 * M / Nn if Nn else 0
        comps = sorted(nx.connected_components(G), key=len, reverse=True)
        giant = G.subgraph(comps[0])
        C = nx.average_clustering(G) if Nn else 0
        L = nx.average_shortest_path_length(giant) if giant.number_of_nodes() > 1 else float('nan')
        C_rand = avg_deg / (Nn - 1) if Nn > 1 else 0
        L_rand = np.log(Nn) / np.log(avg_deg) if avg_deg > 1 else float('nan')
        sigma = (C / C_rand) / (L / L_rand) if C_rand > 0 and not np.isnan(L) else float('nan')
        gamma = fit_powerlaw_exponent(degrees)
        neg_nodes = sum(1 for bg in nodes if bi_val.get(bg, 0.0) < 0)
        neg_occ = sum(doc[bg] for bg in nodes if bi_val.get(bg, 0.0) < 0)
        all_occ = sum(doc[bg] for bg in nodes)
        deg_cent = nx.degree_centrality(G)
        top_deg = sorted(deg_cent, key=deg_cent.get, reverse=True)[:10]
        btw = nx.betweenness_centrality(G, weight=None)
        top_btw = sorted(btw, key=btw.get, reverse=True)[:10]

        metric_rows.append({
            '时期': p, '诗作数': len(texts), '节点': Nn, '边': M,
            '平均度': round(avg_deg, 2), '密度': round(nx.density(G), 4),
            '连通分量': len(comps), '最大连通占比': round(len(comps[0]) / Nn, 3),
            '聚类系数': round(C, 3), '随机聚类基线': round(C_rand, 4),
            '平均最短路径': round(L, 2), '随机路径基线': round(L_rand, 2),
            '小世界系数': round(sigma, 1), '度分布指数(指示性)': gamma,
            '负向节点占比%': round(100 * neg_nodes / Nn, 1),
            '负向意象出现占比%': round(100 * neg_occ / all_occ, 1),
            '度中心前十': '、'.join(top_deg), '介数前十': '、'.join(top_btw)})
        summary.append(f'【{p}】节点{Nn} 边{M} 负向出现占比{100 * neg_occ / all_occ:.0f}%  '
                       f'度前十: {"、".join(top_deg)}')

        # 导出 Gephi 文件
        pd.DataFrame([{'Id': bg, 'Label': bg, 'English': config.TRANS.get(bg, ''),
                       'Frequency': doc[bg], 'Valence': round(bi_val.get(bg, 0.0), 4)}
                      for bg in nodes]
                     ).to_csv(f'{out}/{p}_节点.csv', index=False, encoding='utf-8-sig')
        pd.DataFrame([{'Source': a, 'Target': b, 'Weight': round(w, 4),
                       'Cooccur': c0, 'Type': 'Undirected'} for a, b, w, c0 in edges]
                     ).to_csv(f'{out}/{p}_边.csv', index=False, encoding='utf-8-sig')
        nx.write_gexf(G, f'{out}/{p}_网络.gexf')
        print(f'{p}: {Nn} 节点, {M} 边, 已导出')

    pd.DataFrame(metric_rows).to_csv(f'{out}/时期网络_结构指标.csv',
                                     index=False, encoding='utf-8-sig')
    with open(f'{out}/时期网络_摘要.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary))

    # ---------- 预览图（2×2，只画核心 CORE_TOP_N 节点，其余隐藏） ----------
    for lang in ['en', 'cn']:
        fig, axes = plt.subplots(2, 2, figsize=(17, 15))
        for ax, p in zip(axes.flat, config.PERIODS):
            G_full = graphs[p]
            wdeg_full = {bg: sum(d['weight'] for _, _, d in G_full.edges(bg, data=True))
                         for bg in G_full.nodes}
            keep = set(sorted(wdeg_full, key=wdeg_full.get, reverse=True)[:CORE_TOP_N])
            G = G_full.subgraph(keep).copy()
            pos = nx.spring_layout(G, k=2.4 / math.sqrt(G.number_of_nodes()),
                                   iterations=150, seed=LAYOUT_SEED)
            widths = [G[u][v]['weight'] * 1.6 for u, v in G.edges]
            nx.draw_networkx_edges(G, pos, ax=ax, width=widths,
                                   edge_color='#cccccc', alpha=0.5)
            colors = ['#d4574c' if G.nodes[bg]['valence'] > 0 else '#4a72a6'
                      for bg in G.nodes]
            sizes = [24 + 20 * math.sqrt(G.nodes[bg]['frequency']) for bg in G.nodes]
            nx.draw_networkx_nodes(G, pos, ax=ax, node_color=colors, node_size=sizes,
                                   alpha=0.9, linewidths=0.4, edgecolors='white')
            deg = {bg: sum(d['weight'] for _, _, d in G.edges(bg, data=True))
                   for bg in G.nodes}
            top = sorted(deg, key=deg.get, reverse=True)[:NET_LABEL_TOP]
            for bg in top:
                lab = bg if lang == 'cn' else (f"{bg} ({config.TRANS.get(bg, '')})"
                                               if config.TRANS.get(bg) else bg)
                x, y = pos[bg]
                ax.annotate(lab, (x, y), fontsize=10, fontweight='bold',
                            ha='center', va='center', xytext=(0, 10),
                            textcoords='offset points', color='#111',
                            bbox=dict(boxstyle='round,pad=0.15', fc='white',
                                      ec='none', alpha=0.75))
            niso = G_full.number_of_nodes() - CORE_TOP_N
            title = (f"{config.PERIOD_EN[p]} Tang: core network "
                     f"(top {G.number_of_nodes()} nodes by degree, {G.number_of_edges()} edges)"
                     if lang == 'en'
                     else f'{p}：意象共现网络（核心 {G.number_of_nodes()} 节点，'
                          f'{G.number_of_edges()} 边）')
            if niso > 0:
                title += (f"  [full network: {G_full.number_of_nodes()} nodes]" if lang == 'en'
                          else f'（完整网络 {G_full.number_of_nodes()} 节点，此处仅显示核心）')
            ax.set_title(title, fontsize=13, fontweight='bold')
            ax.axis('off')
        fig.suptitle(
            'Imagery co-occurrence networks of the four Tang periods, core view '
            f'(top {CORE_TOP_N} nodes by degree per period; edges = poem-level NPMI \u2265 {NET_NPMI_MIN}; '
            'red = positive, blue = negative; node size = frequency)' if lang == 'en'
            else f'四期意象共现网络·核心视图（每期度最高的前 {CORE_TOP_N} 个节点及其之间的边；'
                 f'边＝诗级 NPMI≥{NET_NPMI_MIN}；红＝正，蓝＝负；点大小＝频次）',
            fontsize=12.5, y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.98])
        fig.savefig(f'{out}/图_四期意象共现网络_{lang.upper()}.png', dpi=300)
        fig.savefig(f'{out}/图_四期意象共现网络_{lang.upper()}.pdf')
        plt.close(fig)

    print(f'\n全部结果已保存到: {out}')


if __name__ == '__main__':
    main()
