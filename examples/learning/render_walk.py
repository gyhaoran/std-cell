"""Render real GDS polygons as inspectable SVG; not AI or a reconstructed layout.
Only the listed layers are projected; text callouts are pedagogical overlays.
"""
from html import escape
from pathlib import Path
import klayout.db as db

ROOT = Path(__file__).resolve().parents[2]
COLORS = {1:'#72b5dd', 9:'#9254be', 10:'#202838', 11:'#e8b747'}


def panel(cellname, layers, x, title):
    layout = db.Layout()
    layout.read(str(ROOT/f'examples/FreePDK45/gds/{cellname}.gds'))
    cell = layout.top_cell()
    box = cell.bbox()
    scale = min(390/max(box.width(), 1), 490/max(box.height(), 1))
    left = x+60+(390-box.width()*scale)/2
    def xy(point):
        return f'{left+(point.x-box.left)*scale:.3f},{115+(box.top-point.y)*scale:.3f}'
    items = [f'<rect x="{x}" y="65" width="515" height="620" rx="12" fill="#f9fbfe" stroke="#d0d5dd"/>', f'<text x="{x+22}" y="96" font-size="22">{escape(title)}</text>']
    for layer in layers:
        index = layout.find_layer(layer, 0)
        if index is None:
            continue
        region = db.Region(cell.begin_shapes_rec(index))
        for polygon in region.each():
            # These teaching layer shapes have no holes. Refuse silently filling holes.
            assert polygon.holes() == 0
            points = ' '.join(xy(p) for p in polygon.each_point_hull())
            items.append(f'<polygon points="{points}" fill="{COLORS[layer]}" fill-opacity="0.65" stroke="{COLORS[layer]}" stroke-width="1.3"/>')
    if cellname == 'INV_X1' and 11 in layers:
        # Anchor annotations at the actual GDS label coordinates.
        for shape in cell.shapes(layout.find_layer(11,0)).each():
            if not shape.is_text():
                continue
            label = shape.text.string
            px, py = map(float, xy(shape.text.trans.disp).split(','))
            if label not in ('A','ZN','VDD','VSS'):
                continue
            lx = x+35 if label == 'A' else x+415
            end = lx+35 if label == 'A' else lx-8
            items.append(f'<path d="M{px} {py} H{end}" stroke="#344054" stroke-width="1.3"/><circle cx="{px}" cy="{py}" r="3" fill="#172033"/><text x="{lx}" y="{py+7}" font-size="23">{label}</text>')
    if cellname == 'INV_X1' and layers == [1,9]:
        for point, label in [(db.Point(1700,9900),'PMOS 沟道'),(db.Point(1700,2975),'NMOS 沟道')]:
            px, py = map(float,xy(point).split(','))
            items.append(f'<text x="{x+28}" y="{py-8}">{label}</text><path d="M{x+28} {py} H{px}" stroke="#344054" stroke-width="1.3"/><circle cx="{px}" cy="{py}" r="3" fill="#172033"/>')
    items.append(f'<text x="{x+22}" y="644">{escape(cellname)} · 显示层 {", ".join(map(str,layers))}</text>')
    items.append(f'<text x="{x+22}" y="671">原始 DBU = {layout.dbu:g} μm；显示不含全部层</text>')
    return ''.join(items)


def document(title, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 760" role="img" aria-labelledby="t"><title id="t">{escape(title)}</title><rect width="1100" height="760" fill="white"/><g font-family="sans-serif" font-size="18" fill="#172033"><text x="30" y="37" font-size="25">{escape(title)}</text>{body}<text x="35" y="724">蓝：Active 1/0　紫：Poly 9/0　黑：Contact 10/0　黄：Metal1 11/0</text></g></svg>'''


if __name__ == '__main__':
    out = ROOT/'assets/freepdk45'
    (out/'inv_x1-layer-walk.svg').write_text(document('同一 INV_X1：先找沟道，再追连接', panel('INV_X1',[1,9],20,'① Active × Poly：两个沟道')+panel('INV_X1',[1,9,10,11],565,'② 加 Contact/M1：确认四个网络')))
    (out/'inv-strength-compare.svg').write_text(document('不同驱动变体：数栅指，不只看 X 后缀', panel('INV_X1',[1,9,10],20,'INV_X1：Active / Poly / Contact')+panel('INV_X4',[1,9,10],565,'INV_X4：Active / Poly / Contact')))
    print('Rendered two SVGs from bundled GDS polygons')
