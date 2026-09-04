# -*- coding: utf-8 -*-
"""
Task 7: Poet-level imagery co-occurrence networks (real networks)
=================================================================
Supplementary exploration — NOT used in the final paper; kept for follow-up
research.
What it does: builds one real imagery co-occurrence network per poet:
    - nodes: imageries occurring at least NET_NODE_MIN times in the poet's
      corpus (NET_NODE_MIN_WW for Wang Wei, whose corpus is smaller);
      function words in config.EXCLUDE never become nodes;
    - edges: two imageries co-occur in at least NET_CO_MIN poems with a
      poem-level NPMI of at least NET_NPMI_MIN;
    - node attributes: frequency, emotional value; edge attribute: NPMI weight.

Outputs (output/task07_poet_networks/):
  - three files per poet: <poet>_nodes.csv, <poet>_edges.csv,
    <poet>_network.gexf (gexf opens directly in Gephi; the CSVs also load via
    Gephi's spreadsheet import)
  - figure_four_poet_networks_EN/CN.png: 2×2 preview (isolated nodes hidden;
    the top NET_LABEL_TOP highest-degree nodes are labelled)

All thresholds sit at the top of this file; edit and re-run.
Run: python task07_poet_networks.py   (about 2-3 minutes)
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

# ---------- adjustable thresholds ----------
NET_NODE_MIN = 10        # minimum node occurrences (Li Bai, Du Fu, Bai Juyi)
NET_NODE_MIN_WW = 5      # Wang Wei only (small corpus)
NET_NPMI_MIN = 0.3       # minimum edge NPMI
NET_CO_MIN = 2           # minimum shared poems per edge
NET_LABEL_TOP = 8        # labelled highest-degree nodes per panel
LAYOUT_SEED = 42         # layout seed (fixed for a reproducible figure)


def poet_presence(texts, vocab):
    """The set of imageries present in each poem (function words excluded)"""
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
    out = utils.task_outdir('task07_poet_networks')
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
                     ).to_csv(f'{out}/{config.POET_EN[n].replace(" ", "_")}_nodes.csv',
                              index=False, encoding='utf-8-sig')
        pd.DataFrame([{'Source': a, 'Target': b, 'Weight': round(w, 4),
                       'Cooccur': c0, 'Type': 'Undirected'} for a, b, w, c0 in edges]
                     ).to_csv(f'{out}/{config.POET_EN[n].replace(" ", "_")}_edges.csv',
                              index=False, encoding='utf-8-sig')
        nx.write_gexf(G, f'{out}/{config.POET_EN[n].replace(" ", "_")}_network.gexf')
        print(f'{n}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')

    # ---------- preview figure (2×2, isolated nodes hidden) ----------
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
        fig.savefig(f'{out}/figure_four_poet_networks_{lang.upper()}.png', dpi=300)
        fig.savefig(f'{out}/figure_four_poet_networks_{lang.upper()}.pdf')
        plt.close(fig)

    print(f'\nAll results saved to: {out}')


if __name__ == '__main__':
    main()
