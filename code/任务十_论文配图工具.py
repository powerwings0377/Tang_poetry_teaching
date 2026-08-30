# -*- coding: utf-8 -*-
"""
任务十：论文配图工具（总框架图 + 轨迹合并图）
==============================================
不依赖语料，纯绘图脚本，直接运行即可重新生成：
1. 图0_总框架图_EN/CN.png —— 论文 Figure 1（范式总体架构）
2. 图_意象轨迹_合并_EN/CN.png —— 论文 Figure 8（a/b 双面板轨迹图，
   由任务三产出的 图9_意象轨迹 与 图10_意象轨迹 合并而成）
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image, ImageDraw, ImageFont
import os

C_CORPUS = '#5B7A99'; C_ENGINE = '#7A8B6F'; C_APP = '#B08D7E'; C_TEXT = '#333333'
OUT = os.path.dirname(os.path.abspath(__file__))


def draw_framework(texts, outpath, seg_fs, seg_attr_fs, dpi=300):
    fig, ax = plt.subplots(figsize=(13.5, 6.0), dpi=dpi)
    ax.set_xlim(0, 100); ax.set_ylim(0, 46); ax.axis('off')
    W_LIGHT = (1, 1, 1, 0.85)

    def stage_label(x, y, txt):
        ax.text(x, y, txt, ha='left', va='center', fontsize=11.5, fontweight='bold', color=C_TEXT)

    def item(x, y, w, h, name, attr, fc, name_fs=10.5, attr_fs=8.8):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.6,rounding_size=1.2', fc=fc, ec='none', alpha=0.95))
        if attr:
            ax.text(x+w/2, y+h*0.66, name, ha='center', va='center', fontsize=name_fs, fontweight='bold', color='white')
            ax.text(x+w/2, y+h*0.32, attr, ha='center', va='center', fontsize=attr_fs, color=W_LIGHT)
        else:
            ax.text(x+w/2, y+h/2, name, ha='center', va='center', fontsize=name_fs, fontweight='bold', color='white')

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=22, lw=2.2, color='#666666'))

    t = texts
    stage_label(1, 43.5, t['s1'])
    item(1, 26, 19, 12, t['corpus_name'], t['corpus_attr'], C_CORPUS, name_fs=9.5, attr_fs=7.8)
    item(1, 8, 19, 12, t['seg_name'], t['seg_attr'], C_CORPUS, name_fs=seg_fs, attr_fs=seg_attr_fs)
    arrow(10.5, 25.2, 10.5, 20.8)
    stage_label(25, 43.5, t['s2'])
    ax.add_patch(FancyBboxPatch((25, 4), 32, 35, boxstyle='round,pad=0.6,rounding_size=1.2', fc='#EFEFE9', ec='none'))
    item(27, 28, 28, 9, t['m1_name'], t['m1_attr'], C_ENGINE, name_fs=10, attr_fs=8.5)
    item(27, 16.5, 28, 9, t['m2_name'], t['m2_attr'], C_ENGINE, name_fs=10, attr_fs=8.5)
    item(27, 5, 28, 9, t['m3_name'], t['m3_attr'], C_ENGINE, name_fs=10, attr_fs=8.5)
    stage_label(62, 43.5, t['s3'])
    ax.add_patch(FancyBboxPatch((62, 4), 36, 35, boxstyle='round,pad=0.6,rounding_size=1.2', fc='#F3EEE9', ec='none'))
    item(64, 28, 32, 9, t['a1_name'], t['a1_attr'], C_APP, name_fs=9.5, attr_fs=8.5)
    item(64, 16.5, 32, 9, t['a2_name'], t['a2_attr'], C_APP, name_fs=9.5, attr_fs=8.5)
    item(64, 5, 32, 9, t['a3_name'], t['a3_attr'], C_APP, name_fs=9.5, attr_fs=8.5)
    arrow(20.8, 21.5, 24.2, 21.5)
    arrow(57.8, 21.5, 61.2, 21.5)
    ax.plot([80, 80, 10.5, 10.5], [3.2, 2.4, 2.4, 7.4], color='#999999', lw=1.5, linestyle=(0, (5, 4)))
    ax.add_patch(FancyArrowPatch((10.5, 2.4), (10.5, 7.4), arrowstyle='-|>', mutation_scale=16, color='#999999', lw=0))
    ax.text(46, 0.4, t['loop'], ha='center', va='bottom', fontsize=9, color='#777777', style='italic')
    fig.savefig(outpath, bbox_inches='tight', facecolor='white', dpi=dpi)
    plt.close(fig)


EN = dict(s1='1. CORPUS', s2='2. EVIDENCE ENGINE', s3='3. TEACHING APPLICATIONS',
    corpus_name='Complete Tang Poems', corpus_attr='cleaned corpus · 41,821 poems',
    seg_name='Couplet-window segmentation', seg_attr='terminal punctuation · 2 lines per window',
    m1_name='Imagery mining', m1_attr='instruments: BPE + PCI',
    m2_name='Seed-based affective scoring', m2_attr='measure: Emotion Proximity Index (EPI)',
    m3_name='Co-occurrence measurement', m3_attr='measure: Co-occurrence strength (Cooc)',
    a1_name='Case 1: Signature imageries', a1_attr='→ teach poet style',
    a2_name='Case 2: Imagery trajectories', a2_attr='→ teach literary history',
    a3_name='Textbook canon', a3_attr='→ evidence on the poems students read',
    loop='every activity ends by returning to close reading of the poems')

CN = dict(s1='1. 语料', s2='2. 证据引擎', s3='3. 教学应用',
    corpus_name='全唐诗', corpus_attr='清洗后语料 · 41,821 首',
    seg_name='联窗切分', seg_attr='终止标点 · 两句一联',
    m1_name='意象挖掘', m1_attr='工具：BPE ＋ PCI',
    m2_name='种子词情感打分', m2_attr='度量：情感贴近指数（EPI）',
    m3_name='共现测量', m3_attr='度量：共现强度（Cooc）',
    a1_name='案例一：签名意象', a1_attr='→ 教诗人风格',
    a2_name='案例二：意象轨迹', a2_attr='→ 教文学史',
    a3_name='教材正典', a3_attr='→ 用学生读的诗做证据',
    loop='每个活动最后都回到诗歌文本的细读')


def merge_trajectories(pos_png, neg_png, outpath):
    """把任务三的正向/负向两张轨迹图拼成一张 a/b 双面板图（论文 Figure 8）"""
    a = Image.open(pos_png).convert('RGB')
    b = Image.open(neg_png).convert('RGB')
    W = max(a.width, b.width)
    fit = lambda im: im.resize((W, int(im.height*W/im.width)), Image.LANCZOS) if im.width != W else im
    a, b = fit(a), fit(b)
    pad = 30
    canvas = Image.new('RGB', (W, a.height + b.height + pad*3), 'white')
    canvas.paste(a, (0, pad)); canvas.paste(b, (0, a.height + pad*2))
    d = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 64)
    d.text((10, 10), 'a', fill='black', font=font)
    d.text((10, a.height + pad + 10), 'b', fill='black', font=font)
    canvas.save(outpath, dpi=(300, 300), optimize=True)


if __name__ == '__main__':
    draw_framework(EN, f'{OUT}/图0_总框架图_EN.png', seg_fs=8.6, seg_attr_fs=7.2)
    draw_framework(CN, f'{OUT}/图0_总框架图_CN.png', seg_fs=9.5, seg_attr_fs=7.8)
    print('框架图已生成')
    # 轨迹合并图需要先运行任务三得到 图9/图10 后再执行：
    # merge_trajectories('图9_意象轨迹_EN.png', '图10_意象轨迹_EN.png', '图_意象轨迹_合并_EN.png')
    # merge_trajectories('图9_意象轨迹_CN.png', '图10_意象轨迹_CN.png', '图_意象轨迹_合并_CN.png')
