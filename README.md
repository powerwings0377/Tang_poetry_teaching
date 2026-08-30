# 唐诗"特征—证据"教学范式：数据与代码仓库
# Tang Poetry Feature–Evidence Teaching Paradigm: Data & Code Repository

本仓库是论文 *From impression to evidence: a feature-evidence paradigm for teaching Tang poetic style and literary history* 的配套数据与代码，包含全部计算程序、中间过程产物和论文结果图，可用于结果复核、二次开发与教学复用。

This repository accompanies the paper. It contains the full analysis pipeline, intermediate data products, and all paper figures, so that every number and every figure in the paper can be reproduced, reloaded, or extended.

---

## 一、仓库结构 / Repository structure

```
Tang_poetry_teaching/
├── README.md                  ← 本文件
├── code/                      ← 全部计算程序（可直接运行）
│   ├── config.py              ← 全局配置：路径、种子字、排除词、阈值、词表
│   ├── utils.py               ← 公共函数库
│   ├── 任务一_数据准备与时期归属.py
│   ├── 任务二_四诗人风格分析.py
│   ├── 任务三_时期趋势与意象轨迹.py
│   ├── 任务四_共享意象矩阵与自我网络.py
│   ├── 任务五_教材正典证据包.py
│   ├── 任务六_单字共现二元词对比.py
│   ├── 任务七_诗人意象共现网络构建.py   （扩展分析，论文未采用）
│   ├── 任务八_时期意象共现网络构建.py   （扩展分析，论文未采用）
│   ├── 任务九_稳健性检验.py             （阈值敏感性 + 种子敏感性）
│   ├── 任务十_论文配图工具.py           （框架图 + 轨迹合并图，纯绘图）
│   ├── README.md              ← 程序使用说明（详见该文件）
│   └── input/                 ← 输入数据（见第四节）
├── data/                      ← 中间过程产物
│   ├── networks/              ← 四位诗人的意象网络：节点表、边表、gexf
│   ├── validation_records/    ← 验证记录：专家标注表、知网金标准抽样与逐条检索记录、文献意象参考集
│   ├── 稳健性检验结果/         ← 任务九输出：阈值敏感性.txt、种子敏感性.txt
│   ├── 教材正典108首_打分表.csv
│   └── 新实验结果汇总.json
├── figures/
│   ├── paper/                 ← 论文现用图（按图号分文件夹，EN＋CN，PNG＋PDF）
│   └── archive/               ← 过程图与历史版本（火山图、旧版轨迹、其他单字共现等）
└── docs/
```

---

## 二、环境依赖 / Requirements

- Python ≥ 3.8
- 依赖包：`pandas numpy matplotlib openpyxl`
- 可选：`adjustText`（仅任务二的火山图防重叠标注需要；未安装也能正常运行，自动退化）

```bash
pip install pandas numpy matplotlib openpyxl adjustText
```

- 网络图美化使用 Gephi（可选）：`data/networks/` 下的 `*_网络.gexf` 可直接拖入 Gephi 打开。

---

## 三、快速复现 / Quick start

```bash
cd code
python 任务一_数据准备与时期归属.py
python 任务二_四诗人风格分析.py
python 任务三_时期趋势与意象轨迹.py
python 任务四_共享意象矩阵与自我网络.py
python 任务五_教材正典证据包.py
python 任务六_单字共现二元词对比.py
python 任务九_稳健性检验.py
python 任务十_论文配图工具.py
```

各任务的输出写入 `code/output/<任务名>/`。任务七、任务八为扩展分析（网络分析），论文最终版未采用，供后续研究。任务十为纯绘图脚本，不依赖语料。

Run the task scripts in `code/`. Each task writes its outputs to `code/output/<task>/`. Tasks 7–8 (network analysis) are supplementary explorations not used in the final paper; Task 10 is figure-only.

---

## 四、输入数据说明 / Input data

| 文件 | 内容 | 说明 |
|---|---|---|
| `code/input/全唐诗_cleaned.txt` | 清洗后的全唐诗语料，41,821 首 | 格式：`作者#诗题#正文`，一行一首；来源：古诗文网 gushiwen.cn，已去除卷次、标题、注释，繁体转简体 |
| `code/input/单字情感值_扩展后.txt` | 7,050 个单字的情感值词典 | 列：字、扩展后情感值、原始值、联频 |
| `code/input/双字词情感值_扩展_加单个.txt` | 756 个核心诗歌意象的情感值词典 | 列：双字词、情感值（含构词字贡献，可超出 [−1,1]） |
| `code/input/诗人年份-详细.xlsx` | 338 位诗人的生卒年与时期归属 | 时期归属规则见论文 4.2 节（分层规则集） |
| `code/input/教材篇目_110条.csv` | 统编教材唐诗条目清单 | 匹配后 108 首进入正典语料 |

种子字集（正/负各 50 字）写在 `config.py` 的 `POS_SEEDS` / `NEG_SEEDS` 中，与论文补充附录 A 一致。

---

## 五、论文图表对照表 / Paper-to-artifact map

| 论文内容 | 产出程序 | 数据/图文件 |
|---|---|---|
| Figure 1 范式总框架图 | 任务十 `draw_framework` | `figures/paper/Figure1_总框架图/` |
| Figure 2 四诗人箱线图 | 任务二 | `figures/paper/Figure2_四诗人箱线图/` |
| Figure 3 签名意象（12×4） | 任务二 | `figures/paper/Figure3_签名意象/` |
| Figure 4 共享意象矩阵 | 任务四 | `figures/paper/Figure4_共享意象矩阵/` |
| Figure 5 单字"酒"共现 | 任务六 | `figures/paper/Figure5_酒_共现对比/` |
| Figure 6 "故人"共现 | 任务四（自我网络） | `figures/paper/Figure6_故人_共现/` |
| Figure 7 王朝情感曲线 | 任务三 | `figures/paper/Figure7_王朝情感曲线/` |
| Figure 8 意象轨迹（a/b 合并） | 任务三 ＋ 任务十拼图 | `figures/paper/Figure8_意象轨迹_ab/` |
| Figure 9 教材正典对全集 | 任务五 | `figures/paper/Figure9_教材对全集/` |
| 补充表 S1（四诗人统计与检验） | 任务二 | `code/output/任务二*/` |
| 补充表 S2（12 组种子敏感性） | 任务九 | `data/稳健性检验结果/种子敏感性.txt` |
| 阈值敏感性（336 个通过意象） | 任务九 A 部分 | `data/稳健性检验结果/阈值敏感性.txt` |
| 正典逐首打分表 | 任务五 | `data/教材正典108首_打分表.csv` |
| 验证记录（专家标注、知网金标准、kappa） | —（原始记录） | `data/validation_records/` |
| 诗人/时期意象网络（扩展） | 任务七、任务八 | `data/networks/` |

---

## 六、关键数字锚点（供快速核验） / Key numbers for verification

- 语料 41,821 首；联窗 110,110 个；BPE 候选 1,021 个；PCI≥0.00 保留 756 个核心意象
- 双重证据过滤（|v|≥0.3，|c1+c2|≥0.2，符号一致）：336 个意象通过
- 意象库与文献金标准 Cohen's kappa = 0.97（95% CI 0.93–1.00）
- 四诗人诗级情感均值：李白 +0.96、王维 +0.79、杜甫 +0.68、白居易 +0.67
- 四期均值：初唐 +1.77、盛唐 +0.82、中唐 +0.58、晚唐 +0.53（F(3,36644)=387.64）
- 教材正典 108 首均值 −0.03（47.2% 为正）对全集 +0.75（68.5% 为正）
- 种子敏感性（12 组重抽样）：正典<全集 12/12、李白居首 12/12、初唐>盛唐>中唐 12/12、中唐>晚唐 10/12

---

## 七、许可与引用 / License & citation

- 代码：MIT License
- 数据与图表：CC BY 4.0（引用请注明出处）

如使用本仓库，请引用论文（信息以发表版本为准）。If you use this repository, please cite the paper.

---

## 八、常见问题 / FAQ

**图中中文变方框？** 安装任一常见中文字体（微软雅黑、黑体、苹方等）后重跑对应任务。

**任务二火山图标签重叠？** 安装 `adjustText` 后重跑（论文最终版未采用火山图，存档于 `figures/archive/`）。

**想换分析对象（其他诗人/时期/词）？** 只需修改 `config.py` 中的词表与参数（`TRAJ_POS_WORDS`、`MATRIX_WORDS`、`CHAR_TARGETS`、`EXCLUDE` 等），重跑对应任务即可，详见 `code/README.md` 第五节。
