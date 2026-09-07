# 自学实验与结果边界

所有命令从教程根目录运行。正文的 Python 代码以本机 Python 3.12.3 实测；不修改原 LibreCell 仓库，不向共享环境安装依赖。每个输出实验要求新的空目录，避免覆盖历史证据。

| 实验 | 命令入口 | 依赖 | 已核验内容 |
|---|---|---|---|
| 环境盘点 | `python examples/learning/preflight.py` | 标准库 | 只读列出解释器、包版本、工具路径 |
| 图算法 | `python examples/learning/algorithms.py` | 标准库 | Euler 共同顺序、带权最短路、冲突与重布断言 |
| 真实 GDS 分层图 | `python examples/learning/render_walk.py` | KLayout Python 包 | 读取 INV_X1/X4 原始多边形，写两张 SVG |
| 9 点 NLDM | `python examples/learning/characterize.py --output NEW_DIR` | 标准库、ngspice | 36 个测量值及 9 个输入 slew，生成完整层次教学 Liberty |
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

- 全套回归的汇总见 [verification.json](verification.json)；`scripts/verify_learning.py` 每次重跑会把新日志和证据留在独立的 `/tmp/stdcell-learning-check-*` 目录中，不覆盖本次归档。
- `reference-run/`：ngspice 42 的 9 个实测点、每点 deck/log/原始波形，以及 CSV、JSON、Liberty、SVG。Level-1 模型为本教程自拟，不是 FreePDK45。
- `source-reference/`：本地 LibreCell `f708e3a` 原始 `net_util.py` 的修改副本和实际测试摘要。副本保留原上游 GPL 版权声明，完整代码授权请遵循原文件头及上游许可证。
- `geometry-reference/`：自拟孤立方接触孔规则的 GDS 与结果，不是完整 FreePDK45 签核。
- 本机 KLayout Python 包为 0.30.8；ngspice 版本详情和模型 SHA256 写在 `reference-run/provenance.json`。
- 参考 deck 中的 include 是生成当时的绝对路径。换机器请重新运行 `characterize.py`，它根据本机文件位置生成 deck，不要求复制旧路径。

## 没有完成或没有覆盖的事项

当前完整 lclayout 在导入依赖处受缺少 z3/pysmt 阻塞，网络权限不允许安装；不存在“本书已验证的全生成器依赖锁”。这里的实验不声称实现完整新工艺适配、body/L 元数据传递、外部四端 LVS、PEX、功耗/输入电容/顺序约束表征、全库角点覆盖或 P&R 签核。

学习实验使用的 `EDU_INV`、真实 Nangate `INV_X1`、layout 的 dummy `INVX1` 和 librecell-lib 历史 PEX `INVX1` 是不同来源对象，不得把它们的视图混成同一单元的发布包。

## 维护正文

章节正文直接编辑对应 HTML。全书顺序与跳读条件集中在 `scripts/book.py` 的 `BOOK`；修改后执行 `python scripts/book.py`，再运行 `--check`。`--split-legacy` 是已经执行的迁移入口，日常编辑不需要使用。已有页面地址和原分类锚点保留。
