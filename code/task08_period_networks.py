# -*- coding: utf-8 -*-
"""
Task 8: Period-level imagery co-occurrence networks (Early / High / Mid / Late
Tang, one network each)
=====================================================================
Supplementary exploration — NOT used in the final paper; kept for follow-up
research.
What it does: builds one real imagery co-occurrence network per period, with
the same conventions as Task 7:
    - nodes: imageries occurring at least NET_NODE_MIN times in the period's
      corpus (the Early Tang corpus is small but suffices; the same threshold
      is used for all four periods); function words in config.EXCLUDE never
      become nodes;
    - edges: two imageries co-occur in at least NET_CO_MIN poems of the same
      period, with a poem-level NPMI of at least NET_NPMI_MIN;
    - node attributes: frequency, emotional value; edge attribute: NPMI weight.

Outputs (output/task08_period_networks/) — complete data for writing:
  - three files per period: <period>_nodes.csv, <period>_edges.csv,
    <period>_network.gexf (gexf opens directly in Gephi)
  - period_network_metrics.csv: per period — nodes, edges, average degree,
    density, connected components, giant-component share, clustering
    coefficient, random baselines, average shortest path, small-world
    coefficient, degree-distribution exponent, negative-node share,
    negative-occurrence share, top-10 degree hubs, top-10 betweenness
  - period_network_summary.txt: per-period hub words and negative shares
  - figure_four_period_networks_EN/CN.png: 2×2 preview

All thresholds sit at the top of this file; edit and re-run.
Run: python task08_period_networks.py   (about 2-3 minutes)
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
NET_NODE_MIN = 10        # minimum node occurrences (same for all four periods)
NET_NPMI_MIN = 0.3       # minimum edge NPMI
NET_CO_MIN = 2           # minimum shared poems per edge
NET_LABEL_TOP = 8        # labelled highest-degree nodes per panel
LAYOUT_SEED = 42         # layout seed (fixed for a reproducible figure)
CORE_TOP_N = 80          # nodes shown in the preview: the full network is too
                         # dense to read, so the preview draws only the top 80
                         # highest-degree nodes and the edges among them;
                         # metrics are still computed on the full network —
                         # CORE_TOP_N affects display only


def period_presence(texts, vocab):
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


def fit_powerlaw_exponent(degrees, kmin=2):
    """Log-log linear fit estimating the power-law exponent of the degree
    distribution (indicative, for reference only)"""
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
    out = utils.task_outdir('task08_period_networks')
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

        # structural metrics
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
            'Period': p, 'Period_EN': config.PERIOD_EN[p], 'Poems': len(texts),
            'Nodes': Nn, 'Edges': M,
            'Avg_degree': round(avg_deg, 2), 'Density': round(nx.density(G), 4),
            'Components': len(comps), 'Giant_share': round(len(comps[0]) / Nn, 3),
            'Clustering': round(C, 3), 'Clustering_random': round(C_rand, 4),
            'Avg_shortest_path': round(L, 2), 'Path_random': round(L_rand, 2),
            'Smallworld_sigma': round(sigma, 1), 'Degree_exponent_indicative': gamma,
            'Negative_nodes_%': round(100 * neg_nodes / Nn, 1),
            'Negative_occurrences_%': round(100 * neg_occ / all_occ, 1),
            'Top10_degree_hubs': ', '.join(top_deg), 'Top10_betweenness': ', '.join(top_btw)})
        summary.append(f'[{p}] nodes {Nn}, edges {M}, negative-occurrence share '
                       f'{100 * neg_occ / all_occ:.0f}%, top-degree hubs: {", ".join(top_deg)}')

        # export Gephi files
        pen = config.PERIOD_EN[p]
        pd.DataFrame([{'Id': bg, 'Label': bg, 'English': config.TRANS.get(bg, ''),
                       'Frequency': doc[bg], 'Valence': round(bi_val.get(bg, 0.0), 4)}
                      for bg in nodes]
                     ).to_csv(f'{out}/{pen}_nodes.csv', index=False, encoding='utf-8-sig')
        pd.DataFrame([{'Source': a, 'Target': b, 'Weight': round(w, 4),
                       'Cooccur': c0, 'Type': 'Undirected'} for a, b, w, c0 in edges]
                     ).to_csv(f'{out}/{pen}_edges.csv', index=False, encoding='utf-8-sig')
        nx.write_gexf(G, f'{out}/{pen}_network.gexf')
        print(f'{p}: {Nn} nodes, {M} edges, exported')

    pd.DataFrame(metric_rows).to_csv(f'{out}/period_network_metrics.csv',
                                     index=False, encoding='utf-8-sig')
    with open(f'{out}/period_network_summary.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary))

    # ---------- preview figure (2×2; only the CORE_TOP_N core nodes shown) ----------
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
        fig.savefig(f'{out}/figure_four_period_networks_{lang.upper()}.png', dpi=300)
        fig.savefig(f'{out}/figure_four_period_networks_{lang.upper()}.pdf')
        plt.close(fig)

    print(f'\nAll results saved to: {out}')


if __name__ == '__main__':
    main()
