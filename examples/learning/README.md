# 自学实验与结果边界

所有命令从教程根目录运行。正文的 Python 代码以本机 Python 3.12.3 实测；不修改原 LibreCell 仓库，不向共享环境安装依赖。每个输出实验要求新的空目录，避免覆盖历史证据。

| 实验 | 命令入口 | 依赖 | 已核验内容 |
|---|---|---|---|
| 环境盘点 | `python examples/learning/preflight.py` | 标准库 | 只读列出解释器、包版本、工具路径 |
| 图算法 | `python examples/learning/algorithms.py` | 标准库 | Euler 共同顺序、带权最短路、冲突与重布断言 |
| 正文推导与算例 | `python examples/learning/concept_checks.py` | 标准库、本地 CDL | AOI21/TINV/DLH 共 16 种输入条件的理想开关稳态核对、DLH 六组管名覆盖、网格/包围/RC/进位/插值算术 |
| 真实 GDS 分层图 | `python examples/learning/render_walk.py` | KLayout Python 包 | 读取 INV_X1/X4 原始多边形，写两张 SVG |
| 9 点 NLDM | `python examples/learning/characterize.py --output NEW_DIR` | 标准库、ngspice | 36 个测量值及 9 个输入 slew，生成完整层次教学 Liberty |
| 传输门基础 | `python examples/learning/transmission_gate_lab.py --output NEW_DIR` | 标准库、ngspice | 单管/TG 对照、隔离、MUX、静态锁存器，4 组波形和 25 个取样电压 |
| 真实源码解析补丁 | `python examples/learning/source_lab.py --librecell-root /home/jasper/code/github/librecell --output NEW_DIR` | KLayout、NetworkX、给定 LibreCell 源码 | 修改副本，6 项测试，输出统一 diff |
| 孤立接触孔迁移 | `python examples/learning/geometry_lab.py --output NEW_DIR` | KLayout Python 包 | 修改前宽度/包围失败，修改后这两项通过 |
| 全书链接与目录 | `python scripts/book.py --check` | 标准库 | 导航幂等、锚点、本地链接、图片 alt |
| 内容和数值回归 | `python scripts/verify_learning.py` | KLayout、NetworkX、ngspice、liberty-parser | 重新运行教学实验，检查表形状和负例 |

创建输出目录示例：

```bash
TUTORIAL_CHAR_OUT=$(mktemp -d /tmp/stdcell-characterize.XXXXXX)
python examples/learning/characterize.py --output "$TUTORIAL_CHAR_OUT"
```

## 结果来源

- 全套回归的早期归档见 [verification.json](verification.json)，新增传输门章节后的回归汇总见 [tg-reference/tutorial-verification.json](tg-reference/tutorial-verification.json)；`scripts/verify_learning.py` 每次重跑会把新日志和证据留在独立的 `/tmp/stdcell-learning-check-*` 目录中，不覆盖历史归档。
- 2026-09-09 后续章节修订的范围与验证记录见 [自学衔接复查](../../docs/tutorial-beginner-review.md)。`concept_checks.py` 直接读取本地 CDL，枚举内部栅的 0/1 稳态并检查电源连通；这不是模拟瞬态求解，不能证明噪声裕量、保持时间、DRC/LVS 或工艺可制造性。
- `reference-run/`：ngspice 42 的 9 个实测点、每点 deck/log/原始波形，以及 CSV、JSON、Liberty、SVG。Level-1 模型为本教程自拟，不是 FreePDK45。
- `tg-reference/`：ngspice 42 的 4 组瞬态波形、25 个取样电压、完整 deck/log/原始数据与 SVG；模型和电路在 `edu_inv.sp`、`edu_tg.sp`。这是功能和开关直觉实验，不是传播延迟表征或工艺签核；隔离实验的 1 MΩ 是显式教学泄漏通路，不是 PDK 泄漏模型。脚本拒绝非空输出目录，版本和文件 SHA256 记录在其 `provenance.json`。
- `source-reference/`：本地 LibreCell `f708e3a` 原始 `net_util.py` 的修改副本和实际测试摘要。副本保留原上游 GPL 版权声明，完整代码授权请遵循原文件头及上游许可证。
- `geometry-reference/`：自拟孤立方接触孔规则的 GDS 与结果，不是完整 FreePDK45 签核。
- 本机 KLayout Python 包为 0.30.8；ngspice 版本详情和模型 SHA256 写在 `reference-run/provenance.json`。
- 参考 deck 中的 include 是生成当时的绝对路径。换机器请重新运行 `characterize.py`，它根据本机文件位置生成 deck，不要求复制旧路径。
- TG 参考 deck 同样包含生成时的绝对路径，换机器请运行 `transmission_gate_lab.py` 重新生成。正文的 TG 电路/版图、MUX 和反馈示意为原生 SVG；其中版图没有完整工艺层和体接触，不能作为 DRC/LVS 证据。现有 Nangate MUX2_X1 的 GDS/CDL 图片仅用作不同实现的对照，不是 EDU_MUX2 的版图。

## 没有完成或没有覆盖的事项

当前完整 lclayout 在导入依赖处受缺少 z3/pysmt 阻塞，网络权限不允许安装；不存在“本书已验证的全生成器依赖锁”。这里的实验不声称实现完整新工艺适配、body/L 元数据传递、外部四端 LVS、PEX、功耗/输入电容/顺序约束表征、全库角点覆盖或 P&R 签核。

学习实验使用的 `EDU_INV`、真实 Nangate `INV_X1`、layout 的 dummy `INVX1` 和 librecell-lib 历史 PEX `INVX1` 是不同来源对象，不得把它们的视图混成同一单元的发布包。

## 维护正文

章节正文直接编辑对应 HTML。全书顺序与跳读条件集中在 `scripts/book.py` 的 `BOOK`，实际知识依赖维护在 `PREREQUISITES`，不要把上一章机械当作唯一前置知识；修改后执行 `python scripts/book.py`，再运行 `--check`。`--split-legacy` 是已经执行的迁移入口，日常编辑不需要使用。已有页面地址和原分类锚点保留。
