"""A deliberately tiny process-porting geometry experiment, not a PDK deck."""
import argparse
import json
from pathlib import Path
import klayout.db as db


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        p.error('output must be empty')
    reports = {}
    for name, margin_nm in [('before', 5), ('after', 35)]:
        layout = db.Layout()
        layout.dbu = 0.001  # KLayout: micrometers per DBU, NOT meters.
        cell = layout.create_cell('EDU_CONTACT')
        cut = db.Region(db.Box(100, 100, 165, 165))
        metal = db.Region(db.Box(100-margin_nm, 100-margin_nm, 165+margin_nm, 165+margin_nm))
        cell.shapes(layout.layer(10, 0)).insert(cut)
        cell.shapes(layout.layer(11, 0)).insert(metal)
        # Boolean enclosure for this isolated square fixture only.
        # Not an implementation of every directional/EOL enclosure rule.
        enclosure_failure = not (cut.sized(35) - metal).is_empty()
        width_failure = not metal.width_check(100).is_empty()
        reports[name] = {'cut_nm': 65, 'margin_nm': margin_nm, 'metal_nm': 65+2*margin_nm, 'width_fail': width_failure, 'enclosure_fail': enclosure_failure}
        layout.write(str(out/f'{name}.gds'))
    assert reports['before']['width_fail'] and reports['before']['enclosure_fail']
    assert not reports['after']['width_fail'] and not reports['after']['enclosure_fail']
    (out/'results.json').write_text(json.dumps(reports, indent=2)+'\n')
    print('PASS: before fails width+enclosure; after passes these two fixture checks ONLY')


if __name__ == '__main__':
    main()
