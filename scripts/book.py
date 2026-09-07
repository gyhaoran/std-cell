"""Maintain static book navigation. Bodies remain editable HTML, no JS required.

python scripts/book.py             refresh titles, numbering, TOCs, navigation
python scripts/book.py --check     verify links, anchors and generated content
--split-legacy is a one-time migration, protected by per-page insertion markers.
"""
import argparse
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
# filename, title, part, self-test for skipping, observable exercise artifact
BOOK = [
('chapter1.html','标准单元库究竟是什么','建立电路与版图基础','能分别说明 GDS、LEF、CDL、Liberty 的消费者','画出从 RTL 到库视图和验证工具的关系图'),
('foundations.html','电学、逻辑与电路图零基础','建立电路与版图基础','能计算 VGS、分清节点/导线、X/Z 与逻辑极性','完成电压、RC、真值表与交叉导线四组题'),
('chapter2.html','从 MOS 到 CMOS 逻辑','建立电路与版图基础','能推导 INV 的两种稳态并标出 W/L/B','画两张导通路径图并解释体接触'),
('chapter3.html','版图如何变成晶体管','建立电路与版图基础','能由 Active×Poly 数沟道并逐网追踪 Contact/M1','写出一只 MOS 的四端证据表'),
('tools.html','终端、文件与 KLayout 上手实验','建立电路与版图基础','能打开指定 GDS、隐藏图层、量栅长并保存截图','交付 INV_X1 的分层截图、坐标与尺寸记录'),
('chapter4.html','反相器完整读图实验','建立电路与版图基础','能不看答案从版图还原 INV 网表','交付 A、ZN、VDD、VSS 的逐网核对表'),
('chapter5.html','NAND、NOR、传输门与源漏共享','建立电路与版图基础','能区分共享机会、真实共享、TG 与三态反相器','手算 OR2 的共享顺序并解释 TG 两相控制'),
('chapter6.html','一个库要交付哪些视图','建立电路与版图基础','能判断网表模型、Liberty 与工艺 deck 的用途','建立跨视图引脚名和单位一致性表'),
('chapter7.html','读懂 PDK 与设计规则','工艺规则与真实单元','能区分 DBU、制造网格和宽度/间距/包围/EOL','填写一个目标工艺的规则来源与换算表'),
('chapter8.html','DRC、LVS 与 PEX 可执行实验','工艺规则与真实单元','能运行 fixture 并解释每类标记的测量对象','重现 7 个教学 DRC 标记，逐类记录修复方案'),
('chapter9.html','FreePDK45 图谱入口与 MOS 识读','工艺规则与真实单元','能给 51 个单元族分类并说明资料缺口','选一个单元完成器件、网络、尺寸、体端证据表'),
('cells-basic.html','反相器、基本门与驱动强度','工艺规则与真实单元','能推导 NAND/NOR 网络并解释为何大驱动也有代价','完成 INV_X1/X4 和 NAND/NOR 的对照练习'),
('cells-compound.html','AOI/OAI 复合门与逻辑映射','工艺规则与真实单元','能展开 AOI21/OAI21 的 8 行表及串并联网络','写出分组方程、敏化条件与真实应用'),
('cells-select.html','比较、选择、缓冲与三态单元','工艺规则与真实单元','能区分 XOR、MUX、TG、TBUF 的功能与高阻','完成选择信号敏化和双驱动总线状态题'),
('cells-arithmetic.html','半加器、全加器与进位链','工艺规则与真实单元','能用 HA/FA 算两位加法并区分 S/CO 路径','逐位计算一次 3+1，标出进位传播'),
('cells-latches.html','锁存器、反馈与透明窗口','工艺规则与真实单元','能按 G 的相位计算 Q 并说明反馈如何保持','完成带时间顺序的 DLH/DLL 状态表'),
('cells-sequential.html','触发器、扫描链与时钟门控','工艺规则与真实单元','能区分采样、异步控制、扫描与时钟门控检查','完成三拍扫描移位和一段门控时序题'),
('cells-physical.html','常量、填充、体接触与天线单元','工艺规则与真实单元','能说明没有布尔输出的物理单元如何验收','建立 row 拼接与 tap/antenna 验收清单'),
('chapter10.html','算法小白也能用的图论','算法与程序实现','能区分电路图、扩散图和布线资源图','画出 NAND 的两种图并标注顶点/边含义'),
('algorithms-lab.html','亲手运行 Euler 与最短路','算法与程序实现','能手算代价并解释最短边数不一定最小代价','重现脚本断言，并写出每步最短路松弛'),
('chapter11.html','晶体管布局','算法与程序实现','能区分可共享顺序和带上下行对齐的合法布局','比较两个候选排列的断开、宽度和可布线性'),
('chapter12.html','单元内部布线','算法与程序实现','能解释拥塞容量、历史代价和冲突集合','画出两个网络竞争一个资源及拆线重布过程'),
('chapter13.html','固定版本并生成第一个单元','算法与程序实现','有本 commit 成功日志、环境锁与内部 LVS 证据','保存真实运行清单；缺依赖时记录阻塞点而不伪造结果'),
('chapter14.html','技术文件逐字段拆解','算法与程序实现','能追踪 gate_length、W、DBU 与 output_map 的消费点','把一个物理尺寸从 PDK 换算到生成几何'),
('chapter15.html','沿源码走完整流水线','算法与程序实现','能指出模型解析、布线、后处理与 writer 的边界','为需求选择修改模块与对应回归范围'),
('source-lab.html','真实源码补丁：显式 MOS 模型映射','算法与程序实现','能编写负例测试并确认补丁未修改上游仓库','跑通 6 项解析测试并审查生成的统一 diff'),
('chapter16.html','新工艺迁移毕业项目','迁移、表征与验收','已有包含器件/规则/视图/外部验证的迁移矩阵','完成分阶段准入标准，而不只列工具名称'),
('porting-lab.html','工艺迁移小实验与证据分级','迁移、表征与验收','能证明几何改动前后哪些规则改善、哪些未覆盖','重现接触孔包围修复并填写未验证项'),
('simulation.html','从 SPICE deck 到实测翻转波形','迁移、表征与验收','能运行 .tran/.measure 并区分 delay 与 slew','重现 EDU_INV 的 9 个负载/转换时间测点'),
('liberty.html','从正常测量读懂完整 Liberty 层次','迁移、表征与验收','能按 template 查二维表并正确做双线性插值','定位真实测点并计算中间点，列出模型遗漏项'),
('chapter17.html','表征故障排查、签核与库级回归','迁移、表征与验收','能把 1e31 追到单点 deck/波形并说明发布门禁','交付一个失败点的日志、激励、阈值与根因证据'),
('appendix.html','术语、排错树、清单与延伸资源','附录','能准确使用全文术语并找到一手资料','用资源索引补齐自己的最弱环节'),
]
SPLITS = {
 'cells-basic.html': ['inverter','drive-strength','basic-gates'],
 'cells-compound.html': ['complex-gates'],
 'cells-select.html': ['select-compare-buffer','tristate'],
 'cells-arithmetic.html': ['arithmetic-cells'],
 'cells-latches.html': ['latch-cells'],
 'cells-sequential.html': ['sequential-cells'],
 'cells-physical.html': ['physical-cells'],
}


def plain(s):
    return unescape(re.sub('<[^>]*>', '', s)).strip()


def label(i):
    return '附录' if BOOK[i][0] == 'appendix.html' else f'第 {i+1} 章'


def split_legacy():
    source = ROOT/'chapter9.html'
    doc = source.read_text()
    for filename, ids in SPLITS.items():
        target = ROOT/filename
        content = target.read_text()
        if '<!-- LEGACY_SECTIONS -->' not in content:
            continue
        chunks = []
        for anchor in ids:
            pattern = rf'  <h2 id="{anchor}">.*?(?=  <h2)'
            match = re.search(pattern, doc, re.S)
            if not match:
                raise ValueError(f'Cannot locate legacy section {anchor}')
            chunks.append(match[0])
            redirect = f'  <p id="{anchor}">本主题已独立成章：<a href="{filename}#{anchor}">{plain(re.search(r"<h2[^>]*>(.*?)</h2>", match[0], re.S)[1])}</a>。原图、真值表均保留，并补充逐步分析与练习。</p>\n\n'
            doc = doc[:match.start()] + redirect + doc[match.end():]
        target.write_text(content.replace('<!-- LEGACY_SECTIONS -->', '\n'.join(chunks)))
    source.write_text(doc)
    # Reconcile prose references to the old chapter numbers exactly once.
    old_to_new = {int(re.search(r'chapter(\d+)', row[0])[1]): i+1 for i,row in enumerate(BOOK) if row[0].startswith('chapter')}
    for filename, *_ in BOOK:
        path = ROOT/filename
        doc = path.read_text()
        if '<!-- chapter-references-migrated -->' in doc:
            continue
        doc = re.sub(r'第\s*(\d+)\s*([～~—–-])\s*(\d+)\s*章', lambda m: f'第 {old_to_new.get(int(m[1]), int(m[1]))}～{old_to_new.get(int(m[3]), int(m[3]))} 章', doc)
        doc = re.sub(r'第\s*(\d+)\s*章', lambda m: f'第 {old_to_new.get(int(m[1]), int(m[1]))} 章', doc)
        path.write_text(doc.replace('</main>', '<!-- chapter-references-migrated -->\n</main>'))
    index = ROOT/'tutorial_index.html'
    content = index.read_text()
    if '<!-- BOOK_TOC -->' not in content:
        counter = [0]
        def replace_old_toc(match):
            counter[0] += 1
            return '<!-- BOOK_TOC -->' if counter[0] == 1 else ''
        content = re.sub(r'<section class="toc-part">.*?</section>', replace_old_toc, content, flags=re.S)
        if not counter[0]:
            raise ValueError('no old index TOC found')
        index.write_text(content)


def generated(doc, name, text, before):
    block = f'<!-- {name}:start -->\n{text}\n<!-- {name}:end -->'
    pattern = rf'<!-- {name}:start -->.*?<!-- {name}:end -->'
    if re.search(pattern, doc, re.S):
        return re.sub(pattern, lambda _: block, doc, flags=re.S)
    return doc.replace(before, block + '\n' + before, 1)


def transform(i, doc):
    filename, title, part, skip, artifact = BOOK[i]
    heading = f'{label(i)}　{title}'
    doc = re.sub(r'<title>.*?</title>', f'<title>{escape(heading)}</title>', doc, count=1, flags=re.S)
    doc = re.sub(r'<h1>.*?</h1>', f'<h1>{escape(heading)}</h1>', doc, count=1, flags=re.S)
    nav = '<a href="tutorial_index.html">总目录 / 学习路线</a>'
    if i:
        nav = f'<a href="{BOOK[i-1][0]}">← {label(i-1)}</a> · ' + nav
    if i+1 < len(BOOK):
        nav += f' · <a href="{BOOK[i+1][0]}">{label(i+1)} →</a>'
    doc = re.sub(r'<nav class="(top-nav|bottom-nav)"[^>]*>.*?</nav>', lambda m: f'<nav class="{m[1]}" aria-label="全书导航">{nav}</nav>', doc, flags=re.S)
    doc = re.sub(r'<footer>.*?</footer>', f'<footer>{escape(heading)} · 实验状态见总目录</footer>', doc, flags=re.S)
    # Stable IDs are preserved. Only visible numbering follows the current order.
    toc = []
    def section(m):
        attrs, body = m[1], m[2]
        number = len(toc)+1
        body = re.sub(r'^\s*(?:\d+|A)\.\d+\s*', '', body)
        anchor = re.search(r'\bid="([^"]+)"', attrs)
        anchor = anchor[1] if anchor else f'section-{number}'
        if 'id=' not in attrs:
            attrs += f' id="{anchor}"'
        toc.append(f'<li><a href="#{anchor}">{escape(plain(body))}</a></li>')
        prefix = 'A' if filename == 'appendix.html' else str(i+1)
        return f'<h2{attrs}>{prefix}.{number} {body}</h2>'
    doc = re.sub(r'<h2([^>]*)>(.*?)</h2>', section, doc, flags=re.S)
    doc = re.sub(r'(<h3[^>]*>)\d+\.\d+\.\d+\s*', r'\1', doc)
    if filename == 'chapter9.html':
        doc = re.sub(r'(href="cells-[^"]+">)9\.\d+\s*', r'\1', doc)
    previous = f'<a href="{BOOK[i-1][0]}">{BOOK[i-1][1]}</a>' if i else '不要求 EDA 操作经验；从本章建立全局地图'
    guide = f'''<aside class="learning-guide" aria-label="分层学习指南">
<p><strong>前置知识：</strong>{previous}。若遇到电压/电容/逻辑符号障碍，返回<a href="foundations.html">电学与电路图基础</a>；工具操作不熟，返回<a href="tools.html">工具上手</a>。</p>
<p><strong>快速跳过条件：</strong>{escape(skip)}。不能独立完成时，请按正文顺序学。</p>
<p><strong>本章验收：</strong>{escape(artifact)}。先做题，再展开答案；只读过不算完成。</p>
<details><summary>本章导航 · 已熟悉的内容可以直接跳过</summary><ol>{''.join(toc)}</ol></details>
</aside>'''
    return generated(doc, 'learning-guide', guide, '<h2')


def index_block():
    parts = []
    previous = None
    for i, (filename, title, part, skip, artifact) in enumerate(BOOK):
        if part != previous:
            if previous:
                parts.append('</ul></section>')
            parts.append(f'<section class="toc-part"><h2>{part}</h2><ul class="toc-list">')
            previous = part
        parts.append(f'<li><a href="{filename}"><strong>{label(i)}　{title}</strong><small>{artifact}</small></a></li>')
    parts.append('</ul></section>')
    return '\n'.join(parts)


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs, self.errors = set(), [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                self.errors.append(f'duplicate id {attrs["id"]}')
            self.ids.add(attrs['id'])
        for key in ('href','src'):
            if key in attrs:
                self.refs.append(attrs[key])
        if tag == 'img' and not attrs.get('alt'):
            self.errors.append('image without alt text')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    p.add_argument('--split-legacy', action='store_true')
    args = p.parse_args()
    if args.split_legacy:
        if args.check:
            p.error('migration and read-only check are mutually exclusive')
        split_legacy()
    errors = []
    for i, (filename, *_) in enumerate(BOOK):
        path = ROOT/filename
        doc = path.read_text()
        result = transform(i, doc)
        if args.check:
            if doc != result:
                errors.append(f'{filename}: navigation is stale; run scripts/book.py')
        else:
            path.write_text(result)
    index = ROOT/'tutorial_index.html'
    content = index.read_text()
    new_index = generated(content, 'book-toc', index_block(), '<!-- BOOK_TOC -->')
    new_index = re.sub(r'[ \t]+$', '', new_index, flags=re.M)
    if args.check:
        if content != new_index:
            errors.append('index TOC is stale')
    else:
        index.write_text(new_index)
    parsed = {}
    for path in ROOT.glob('*.html'):
        parser = References()
        parser.feed(path.read_text())
        parsed[path.resolve()] = parser
        errors.extend(f'{path.name}: {error}' for error in parser.errors)
    for path, parser in parsed.items():
        for ref in parser.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                continue
            target = (path.parent/unquote(url.path)).resolve() if url.path else path
            if not target.exists():
                errors.append(f'{path.name}: missing {ref}')
            elif url.fragment and target in parsed and unquote(url.fragment) not in parsed[target].ids:
                errors.append(f'{path.name}: missing anchor {ref}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(BOOK)} reading units, navigation, local links, anchors, image alt text')


if __name__ == '__main__':
    main()
