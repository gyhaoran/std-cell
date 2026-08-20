# Create a tiny GDS with deliberate violations for dummy_tech_checks.drc.
# Coordinates are in nanometers because layout.dbu is 0.001 micrometers.

include RBA

raise "Pass -rd output=path/to/fixture.gds" unless $output

layout = Layout.new
layout.dbu = 0.001
top = layout.create_cell("DRC_FIXTURE")

ndiff = layout.layer(1, 0)
poly = layout.layer(3, 0)
metal1 = layout.layer(6, 0)
via1 = layout.layer(7, 0)

# Gate length is 40 nm: below the dummy-tech 50 nm check.
top.shapes(ndiff).insert(Box.new(0, 600, 400, 800))
top.shapes(poly).insert(Box.new(180, 500, 220, 900))

# First M1 rectangle is 80 nm wide; the 40 nm gap is also too small.
top.shapes(metal1).insert(Box.new(0, 0, 80, 400))
top.shapes(metal1).insert(Box.new(120, 0, 220, 400))

# Via1 is only 80 nm square.
top.shapes(via1).insert(Box.new(500, 0, 580, 80))

layout.write($output)
