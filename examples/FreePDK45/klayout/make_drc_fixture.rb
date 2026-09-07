# Make a tiny GDS containing deliberate FreePDK45 teaching-rule violations.
# Run with: klayout -b -r make_drc_fixture.rb -rd output=/tmp/fixture.gds

include RBA

output = $output || "/tmp/freepdk45-drc-fixture.gds"
layout = Layout.new
layout.dbu = 0.0001
cell = layout.create_cell("DRC_FIXTURE")

def box_um(cell, layer, layout, x1, y1, x2, y2)
  scale = 1.0 / layout.dbu
  cell.shapes(layer).insert(
    Box.new(
      (x1 * scale).round,
      (y1 * scale).round,
      (x2 * scale).round,
      (y2 * scale).round
    )
  )
end

active = layout.layer(1, 0)
pwell = layout.layer(2, 0)
nwell = layout.layer(3, 0)
poly = layout.layer(9, 0)
contact = layout.layer(10, 0)
metal1 = layout.layer(11, 0)

box_um(cell, pwell, layout, 0.0, 0.0, 2.0, 1.5)
box_um(cell, active, layout, 0.2, 0.2, 0.26, 1.1) # width 0.06 < 0.09
box_um(cell, nwell, layout, 1.6, 0.9, 3.2, 2.2)    # overlaps P-well
box_um(cell, poly, layout, 0.6, 0.2, 0.64, 1.2)   # width 0.04 < 0.05
box_um(cell, metal1, layout, 1.0, 0.2, 1.04, 1.2) # width 0.04 < 0.065
box_um(cell, metal1, layout, 2.0, 0.2, 2.2, 0.8)
box_um(cell, metal1, layout, 2.24, 0.2, 2.44, 0.8) # spacing 0.04 < 0.065
box_um(cell, contact, layout, 2.7, 0.3, 2.75, 0.35) # 0.05 square

layout.write(output)
puts output
