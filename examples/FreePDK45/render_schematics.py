"""Render transistor schematics from the bundled CDL with OpenSchematic.

Run this script from the OpenSchematic repository so its package is importable:

  QT_QPA_PLATFORM=offscreen python \
    /home/jasper/code/docs/std-cell/examples/FreePDK45/render_schematics.py \
    /home/jasper/code/docs/std-cell/examples/FreePDK45/NangateOpenCellLibrary.cdl \
    /tmp/schematics INV_X1 NAND2_X1
"""

import argparse
from pathlib import Path

from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QApplication

from openschematic.controller import SchematicController, SchematicViewMode
from openschematic.ui.schematic_scene import SchematicScene


parser = argparse.ArgumentParser()
parser.add_argument("netlist", type=Path)
parser.add_argument("output_dir", type=Path)
parser.add_argument("cells", nargs="+")
args = parser.parse_args()

app = QApplication.instance() or QApplication([])
controller = SchematicController()
controller.load_file(args.netlist)
args.output_dir.mkdir(parents=True, exist_ok=True)

for cell in args.cells:
    result = controller.show_cell(cell, SchematicViewMode.RECOGNIZED)
    scene = SchematicScene()
    scene.set_cell_layout(result.layout)
    source = scene.sceneRect()
    scale = min(
        1.0,
        2400 / max(source.width(), 1),
        1600 / max(source.height(), 1),
    )
    width = max(1, round(source.width() * scale))
    height = max(1, round(source.height() * scale))
    image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    image.fill(scene.theme.background)

    painter = QPainter(image)
    try:
        scene.render(painter, QRectF(0, 0, width, height), source)
    finally:
        painter.end()

    output = args.output_dir / f"{cell.lower()}-schematic.png"
    if not image.save(str(output), "PNG"):
        raise RuntimeError(f"Failed to save {output}")
    print(output.resolve())
