# Render the GDS already loaded by KLayout. Example:
# QT_QPA_PLATFORM=offscreen klayout -z -nc -rx \
#   -l examples/FreePDK45/freepdk45.lyp \
#   examples/FreePDK45/gds/INV_X1.gds \
#   -r examples/FreePDK45/render_layout.rb \
#   -rd output=/tmp/INV_X1-layout.png

include RBA

view = Application.instance.main_window.current_view
raise "No layout view: load a GDS before this macro" if view.nil?

cell = view.active_cellview.cell
raise "No active cell" if cell.nil?

bbox = cell.bbox
aspect = bbox.empty? ? 1.0 : bbox.width.to_f / [bbox.height, 1].max
height = 900
width = [[(height * aspect).round, 620].max, 1500].min

view.max_hier
view.set_config("grid-visible", "false")
view.set_config("background-color", "#ffffff")
view.zoom_fit
view.save_image($output, width, height)
puts "Rendered #{cell.name}: #{$output} (#{width}x#{height})"
