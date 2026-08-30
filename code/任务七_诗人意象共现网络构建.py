# -*- coding: utf-8 -*-
"""
任务七：诗人意象共现网络构建（真实网络）
================================
做什么：
  为四位诗人各建一张真实的意象共现网络：
    - 节点：该诗人语料中出现不少于 NET_NODE_MIN 次的意象（王维用 NET_NODE_MIN_WW，
      因其语料小）；config.EXCLUDE 里的功能词一律不作节点；
    - 边：两个意象在同一首诗里共现至少 NET_CO_MIN 次，且诗级归一化点互信息
      NPMI ≥ NET_NPMI_MIN；
    - 节点属性：频次、情感值；边属性：NPMI 权重。

输出（output/任务七/）：
  - 每位诗人三个文件：{诗人}_节点.csv、{诗人}_边.csv、{诗人}_网络.gexf
    （gexf 可直接拖进 Gephi 美化；csv 也可用 Gephi 的"导入电子表格"读入）
  - 图_四诗人意象共现网络_EN/CN.png：2×2 预览图（隐藏孤立节点，
    每面板标注度最高的前 NET_LABEL_TOP 个节点）

阈值都在本文件顶部，改完重跑即可。
运行：python 任务七_诗人意象共现网络构建.py   （约2-3分钟）
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
NET_NODE_MIN = 10        # 节点最低出现次数（李、杜、白）
NET_NODE_MIN_WW = 5      # 王维专用（语料小）
NET_NPMI_MIN = 0.3       # 边最低 NPMI
NET_CO_MIN = 2           # 边最低共现诗数
NET_LABEL_TOP = 8        # 每面板标注的高度数节点数
LAYOUT_SEED = 42         # 布局随机种子（固定后可复现同一张图）


def poet_presence(texts, vocab):
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


def build_network(texts, node_min):
    pres = poet_presence(texts, set(utils.load_dicts()[1].keys()))
    N = len(pres)
    doc = Counter()
    for s in pres:
        for bg in s:
            doc[bg] += 1
    nodes = [bg for bg, c in doc.items() if c >= node_min]
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
    out = utils.task_outdir('任务七_诗人意象共现网络构建')
    poems = utils.load_corpus()
    _, bi_val = utils.load_dicts()

    graphs = {}
    for n in config.POETS:
        nmin = NET_NODE_MIN_WW if n == '王维' else NET_NODE_MIN
        texts = [t for a, _, t in poems if a == n]
        nodes, doc, edges = build_network(texts, nmin)
        G = nx.Graph()
        for bg in nodes:
            G.add_node(bg, frequency=doc[bg], valence=bi_val.get(bg, 0.0),
                       english=config.TRANS.get(bg, ''))
        for a, b, w, c0 in edges:
            G.add_edge(a, b, weight=w, co=c0)
        graphs[n] = G
        pd.DataFrame([{'Id': bg, 'Label': bg, 'English': config.TRANS.get(bg, ''),
                       'Frequency': doc[bg], 'Valence': round(bi_val.get(bg, 0.0), 4)}
                      for bg in nodes]
                     ).to_csv(f'{out}/{n}_节点.csv', index=False, encoding='utf-8-sig')
        pd.DataFrame([{'Source': a, 'Target': b, 'Weight': round(w, 4),
                       'Cooccur': c0, 'Type': 'Undirected'} for a, b, w, c0 in edges]
                     ).to_csv(f'{out}/{n}_边.csv', index=False, encoding='utf-8-sig')
        nx.write_gexf(G, f'{out}/{n}_网络.gexf')
        print(f'{n}: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边')

    # ---------- 预览图（2×2，隐藏孤立节点） ----------
    for lang in ['en', 'cn']:
        fig, axes = plt.subplots(2, 2, figsize=(17, 15))
        for ax, n in zip(axes.flat, config.POETS):
            G_full = graphs[n]
            G = G_full.subgraph([bg for bg in G_full.nodes if G_full.degree(bg) > 0]).copy()
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
            niso = G_full.number_of_nodes() - G.number_of_nodes()
            title = (f"{config.POET_EN[n]}: imagery co-occurrence network "
                     f"({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)"
                     if lang == 'en'
                     else f'{n}：意象共现网络（{G.number_of_nodes()} 节点，'
                          f'{G.number_of_edges()} 边）')
            if niso:
                title += (f"  [{niso} isolated nodes hidden]" if lang == 'en'
                          else f'（隐藏孤立节点 {niso} 个）')
            ax.set_title(title, fontsize=13, fontweight='bold')
            ax.axis('off')
        fig.suptitle(
            'Imagery co-occurrence networks of the four poets '
            f'(edges = poem-level NPMI \u2265 {NET_NPMI_MIN}; red = positive, '
            'blue = negative; node size = frequency)' if lang == 'en'
            else f'四诗人意象共现网络（边＝诗级 NPMI≥{NET_NPMI_MIN}；'
                 '红＝正，蓝＝负；点大小＝频次）',
            fontsize=12.5, y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.98])
        fig.savefig(f'{out}/图_四诗人意象共现网络_{lang.upper()}.png', dpi=300)
        fig.savefig(f'{out}/图_四诗人意象共现网络_{lang.upper()}.pdf')
        plt.close(fig)

    print(f'\n全部结果已保存到: {out}')


if __name__ == '__main__':
    main()
