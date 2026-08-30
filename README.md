# Tang Poetry Feature–Evidence Teaching Paradigm: Data & Code Repository
# 唐诗"特征—证据"教学范式：数据与代码仓库

**EN** This repository accompanies the paper *From impression to evidence: a feature-evidence paradigm for teaching Tang poetic style and literary history*. It contains the full analysis pipeline, intermediate data products, and all paper figures, so that every number and every figure in the paper can be reproduced, reloaded, or extended.

**中** 本仓库是论文《从印象到证据：一种面向唐诗风格与文学史教学的"特征—证据"范式》的配套数据与代码，包含全部计算程序、中间过程产物和论文结果图，可用于结果复核、二次开发与教学复用。

---

## 1. Repository structure / 仓库结构

```
Tang_poetry_teaching/
├── README.md                  ← this file / 本文件
├── code/                      ← all analysis scripts, ready to run / 全部计算程序（可直接运行）
│   ├── config.py              ← global configuration: paths, seeds, exclusions, thresholds / 全局配置：路径、种子字、排除词、阈值、词表
│   ├── utils.py               ← shared utilities / 公共函数库
│   ├── 任务一_数据准备与时期归属.py          (Task 1: data preparation & period assignment / 数据准备与时期归属)
│   ├── 任务二_四诗人风格分析.py              (Task 2: four-poet style analysis / 四诗人风格分析)
│   ├── 任务三_时期趋势与意象轨迹.py          (Task 3: period trends & imagery trajectories / 时期趋势与意象轨迹)
│   ├── 任务四_共享意象矩阵与自我网络.py      (Task 4: shared-imagery matrix & ego networks / 共享意象矩阵与自我网络)
│   ├── 任务五_教材正典证据包.py              (Task 5: textbook-canon evidence package / 教材正典证据包)
│   ├── 任务六_单字共现二元词对比.py          (Task 6: character-level co-occurrence / 单字共现对比)
│   ├── 任务七_诗人意象共现网络构建.py        (Task 7: poet imagery networks / 诗人意象网络, supplementary exploration 扩展分析，论文未采用)
│   ├── 任务八_时期意象共现网络构建.py        (Task 8: period imagery networks / 时期意象网络, supplementary exploration 扩展分析，论文未采用)
│   ├── 任务九_稳健性检验.py                  (Task 9: robustness checks / 稳健性检验)

│   ├── README.md              ← program usage guide (Chinese) / 程序使用说明
│   └── input/                 ← input data (see Section 4) / 输入数据（见第四节）
├── data/                      ← intermediate data products / 中间过程产物
│   ├── networks/              ← imagery networks of the four poets: node tables, edge tables, gexf / 四位诗人的意象网络：节点表、边表、gexf
│   ├── validation_records/    ← validation records: expert annotation, gold-standard sample & search records, literature reference set / 验证记录：专家标注表、知网金标准抽样与逐条检索记录、文献意象参考集
│   ├── 稳健性检验结果/         ← Task-9 outputs: threshold sensitivity, seed sensitivity / 阈值敏感性.txt、种子敏感性.txt
│   ├── 教材正典108首_打分表.csv ← per-poem canon scoring table / 教材正典108首逐首打分表
│   └── 新实验结果汇总.json     ← consolidated experimental results / 新实验结果汇总
├── figures/
│   ├── paper/                 ← the nine paper figures, one folder per figure, EN + CN, PNG + PDF / 论文现用图（按图号分文件夹，EN＋CN，PNG＋PDF）
│   └── archive/               ← process figures and earlier versions / 过程图与历史版本
└── docs/
```

---

## 2. Requirements / 环境依赖

**EN** Python ≥ 3.8; packages: `pandas numpy matplotlib openpyxl`; optional: `adjustText` (used only for the non-overlapping labels of the volcano plot in Task 2 — the script runs fine without it). Optional: Gephi for the network files (`data/networks/*_网络.gexf` open directly in Gephi).

**中** Python ≥ 3.8；依赖包：`pandas numpy matplotlib openpyxl`；可选：`adjustText`（仅任务二的火山图防重叠标注需要；未安装也能正常运行，自动退化）。网络图美化使用 Gephi（可选）：`data/networks/` 下的 `*_网络.gexf` 可直接拖入 Gephi 打开。

```bash
pip install pandas numpy matplotlib openpyxl adjustText
```

---

## 3. Quick start / 快速复现

```bash
cd code
python 任务一_数据准备与时期归属.py
python 任务二_四诗人风格分析.py
python 任务三_时期趋势与意象轨迹.py
python 任务四_共享意象矩阵与自我网络.py
python 任务五_教材正典证据包.py
python 任务六_单字共现二元词对比.py
python 任务九_稳健性检验.py
```

**EN** Each task writes its outputs to `code/output/<task>/`. Tasks 7–8 (network analysis) are supplementary explorations not used in the final paper; Task 10 is figure-only.

**中** 各任务的输出写入 `code/output/<任务名>/`。任务七、任务八为扩展分析（网络分析），论文最终版未采用，供后续研究。任务十为纯绘图脚本，不依赖语料。

---

## 4. Input data / 输入数据说明

| File 文件 | Content 内容 | Notes 说明 |
|---|---|---|
| `code/input/全唐诗_cleaned.txt` | Cleaned Complete Tang Poems corpus, 41,821 poems / 清洗后的全唐诗语料 | Format 格式：`作者#诗题#正文`, one poem per line 一行一首；source 来源：gushiwen.cn, cleaned of volume markers, titles, annotations; traditional characters converted to simplified 已去除卷次、标题、注释，繁体转简体 |
| `code/input/单字情感值_扩展后.txt` | Emotional-value dictionary of 7,050 characters / 7,050 个单字的情感值词典 | Columns 列：character 字, extended value 扩展后情感值, raw value 原始值, window frequency 联频 |
| `code/input/双字词情感值_扩展_加单个.txt` | Emotional-value dictionary of 756 core poetic imageries / 756 个核心诗歌意象的情感值词典 | Columns 列：bigram 双字词, value 情感值（含构词字贡献，可超出 [−1,1]） |
| `code/input/诗人年份-详细.xlsx` | Birth/death years and period assignment of 338 poets / 338 位诗人的生卒年与时期归属 | Assignment rules in Section 4.2 of the paper 时期归属规则见论文 4.2 节 |
| `code/input/教材篇目_110条.csv` | List of 110 Tang-poem items in the centrally compiled textbooks / 统编教材唐诗条目清单 | 108 items matched into the canon corpus 匹配后 108 首进入正典语料 |

**EN** The seed sets (50 positive, 50 negative) are in `config.py` (`POS_SEEDS` / `NEG_SEEDS`), identical to Supplementary Appendix A of the paper.

**中** 种子字集（正/负各 50 字）写在 `config.py` 的 `POS_SEEDS` / `NEG_SEEDS` 中，与论文补充附录 A 一致。

---

## 5. Paper-to-artifact map / 论文图表对照表

| Paper content 论文内容 | Producing script 产出程序 | Data / figure file 数据/图文件 |
|---|---|---|
| Figure 1 paradigm architecture 总框架图 | PowerPoint Drawing | `figures/paper/Figure1_总框架图/` |
| Figure 2 four-poet boxplots 四诗人箱线图 | Task 2 任务二 | `figures/paper/Figure2_四诗人箱线图/` |
| Figure 3 signature imageries (12×4) 签名意象 | Task 2 任务二 | `figures/paper/Figure3_签名意象/` |
| Figure 4 shared-imagery matrix 共享意象矩阵 | Task 4 任务四 | `figures/paper/Figure4_共享意象矩阵/` |
| Figure 5 companions of 酒 (wine) 单字"酒"共现 | Task 6 任务六 | `figures/paper/Figure5_酒_共现对比/` |
| Figure 6 companions of 故人 (old friend) "故人"共现 | Task 4 (ego networks) 任务四（自我网络） | `figures/paper/Figure6_故人_共现/` |
| Figure 7 dynasty-level emotional curve 王朝情感曲线 | Task 3 任务三 | `figures/paper/Figure7_王朝情感曲线/` |
| Figure 8 imagery trajectories (panels a/b) 意象轨迹 | Task 3 + Task 10 merge 任务三＋任务十拼图 | `figures/paper/Figure8_意象轨迹_ab/` |
| Figure 9 textbook canon vs. complete works 教材对全集 | Task 5 任务五 | `figures/paper/Figure9_教材对全集/` |
| Supplementary Table S1 (poet statistics & tests) 补充表S1 | Task 2 任务二 | `code/output/任务二*/` |
| Supplementary Table S2 (12 seed configurations) 补充表S2 | Task 9 任务九 | `data/稳健性检验结果/种子敏感性.txt` |
| Threshold sensitivity (336 passing imageries) 阈值敏感性 | Task 9, part A 任务九A部分 | `data/稳健性检验结果/阈值敏感性.txt` |
| Per-poem canon scoring 正典逐首打分表 | Task 5 任务五 | `data/教材正典108首_打分表.csv` |
| Validation records (expert annotation, gold standard, kappa) 验证记录 | — (original records 原始记录) | `data/validation_records/` |
| Poet/period imagery networks (extended) 诗人/时期网络（扩展） | Tasks 7–8 任务七、任务八 | `data/networks/` |

---

## 6. Key numbers for verification / 关键数字锚点（供快速核验）

- Corpus 41,821 poems; 110,110 couplet windows; 1,021 BPE candidates; 756 core imageries retained at PCI ≥ 0.00
- 语料 41,821 首；联窗 110,110 个；BPE 候选 1,021 个；PCI≥0.00 保留 756 个核心意象
- Double-evidence filter (|v|≥0.3, |c1+c2|≥0.2, sign agreement): 336 imageries pass
- 双重证据过滤（|v|≥0.3，|c1+c2|≥0.2，符号一致）：336 个意象通过
- Imagery inventory vs. the literature-based gold standard: Cohen's kappa = 0.97 (95% CI 0.93–1.00)
- 意象库与文献金标准 Cohen's kappa = 0.97（95% CI 0.93–1.00）
- Poem-level means: Li Bai +0.96, Wang Wei +0.79, Du Fu +0.68, Bai Juyi +0.67
- 四诗人诗级情感均值：李白 +0.96、王维 +0.79、杜甫 +0.68、白居易 +0.67
- Period means: Early Tang +1.77, High +0.82, Mid +0.58, Late +0.53 (F(3,36644) = 387.64)
- 四期均值：初唐 +1.77、盛唐 +0.82、中唐 +0.58、晚唐 +0.53（F(3,36644)=387.64）
- Textbook canon (108 poems) mean −0.03 (47.2% positive) vs. full corpus +0.75 (68.5% positive)
- 教材正典 108 首均值 −0.03（47.2% 为正）对全集 +0.75（68.5% 为正）
- Seed sensitivity (12 resampled configurations): canon < corpus 12/12; Li Bai top-ranked 12/12; Early > High > Mid 12/12; Mid > Late 10/12
- 种子敏感性（12 组重抽样）：正典<全集 12/12、李白居首 12/12、初唐>盛唐>中唐 12/12、中唐>晚唐 10/12

---

## 7. License & citation / 许可与引用

**EN** Code: MIT License. Data and figures: CC BY 4.0 (please cite the paper when reusing). If you use this repository, please cite the paper (details to follow the published version).

**中** 代码：MIT License；数据与图表：CC BY 4.0（引用请注明出处）。如使用本仓库，请引用论文（信息以发表版本为准）。

---

## 8. FAQ / 常见问题

**EN**
- **Chinese characters show as boxes in figures?** Install any common Chinese font (Microsoft YaHei, SimHei, PingFang, etc.) and re-run the task.
- **Volcano-plot labels overlap?** Install `adjustText` and re-run Task 2 (the volcano plot was not used in the final paper; archived in `figures/archive/`).
- **Want to analyse other poets, periods, or words?** Edit only the word lists and parameters in `config.py` (`TRAJ_POS_WORDS`, `MATRIX_WORDS`, `CHAR_TARGETS`, `EXCLUDE`, etc.) and re-run the corresponding task; see Section 5 of `code/README.md`.

**中**
- **图中中文变方框？** 安装任一常见中文字体（微软雅黑、黑体、苹方等）后重跑对应任务。
- **任务二火山图标签重叠？** 安装 `adjustText` 后重跑（论文最终版未采用火山图，存档于 `figures/archive/`）。
- **想换分析对象（其他诗人/时期/词）？** 只需修改 `config.py` 中的词表与参数（`TRAJ_POS_WORDS`、`MATRIX_WORDS`、`CHAR_TARGETS`、`EXCLUDE` 等），重跑对应任务即可，详见 `code/README.md` 第五节。
