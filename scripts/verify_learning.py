"""Re-run tutorial evidence. Requires ngspice, KLayout, liberty-parser.

All generated test evidence goes into a new /tmp directory. No upstream writes.
"""
import importlib.util
import json
import math
from pathlib import Path
import re
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from book import BOOK, ROOT
from liberty.parser import parse_liberty


def run(args, cwd=ROOT):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, env={**os.environ, 'QT_QPA_PLATFORM':'offscreen'})
    if result.returncode:
        raise RuntimeError(f'{args}\n{result.stdout}\n{result.stderr}')
    return result.stdout + result.stderr


def main():
    out = Path(tempfile.mkdtemp(prefix='stdcell-learning-check-'))
    logs = {}
    logs['book'] = run([sys.executable,'scripts/book.py','--check'])
    logs['algorithms'] = run([sys.executable,'examples/learning/algorithms.py'])
    logs['source'] = run([sys.executable,'examples/learning/source_lab.py','--librecell-root','/home/jasper/code/github/librecell','--output',str(out/'source')])
    logs['geometry'] = run([sys.executable,'examples/learning/geometry_lab.py','--output',str(out/'geometry')])
    logs['simulation'] = run([sys.executable,'examples/learning/characterize.py','--output',str(out/'simulation')])
    sim = out/'simulation'
    measurements = json.loads((sim/'measurements.json').read_text())
    lib = parse_liberty((sim/'edu_inv.lib').read_text())
    timing = lib.get_group('cell','EDU_INV').get_group('pin','Y').get_group('timing')
    for name in ['cell_rise','cell_fall','rise_transition','fall_transition']:
        table = timing.get_group(name).get_array('values')
        assert table.shape == (3,3)
        for row, slew in enumerate([20,80,200]):
            for col, load in enumerate([5,20,50]):
                value = table[row,col]
                assert math.isfinite(value) and 0 < value < 1
                assert math.isclose(value, measurements[f'{slew}ps_{load}ff'][name]*1e9, rel_tol=1e-7)
    values = timing.get_group('cell_rise').get_array('values')
    interpolation = sum(values[r,c] for r in [0,1] for c in [0,1])/4
    assert abs(interpolation - 0.0269221975) < 1e-7
    # A deliberately invalid stimulus never reaches the 50% trigger voltage.
    module_path = ROOT/'examples/learning/characterize.py'
    spec = importlib.util.spec_from_file_location('tutorial_characterizer',module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    bad = out/'no-transition'
    bad.mkdir()
    (bad/'test.sp').write_text(module.deck(80,20).replace('PULSE(0 1.8','PULSE(0 0.2'))
    run(['ngspice','-b','-o','run.log','test.sp'],cwd=bad)
    bad_log = (bad/'run.log').read_text()
    assert not re.search(r'^\s*cell_fall\s*=\s*[0-9]',bad_log,re.M)
    assert 'failed' in bad_log.lower() or 'out of interval' in bad_log.lower()
    # Reproduce the existing FreePDK45 deliberately-invalid DRC fixture.
    logs['drc_fixture'] = run(['klayout','-b','-r','examples/FreePDK45/klayout/make_drc_fixture.rb','-rd',f'output={out}/fixture.gds'])
    logs['drc'] = run(['klayout','-b','-r','examples/FreePDK45/klayout/freepdk45_teaching_subset.drc','-rd',f'input={out}/fixture.gds','-rd',f'report={out}/fixture.lyrdb'])
    items = ET.parse(out/'fixture.lyrdb').findall('.//items/item')
    assert len(items) == 7
    categories = {}
    for item in items:
        category = item.findtext('category').strip("'")
        categories[category] = categories.get(category,0)+1
    assert categories == {'Well.1':1,'Active.1':1,'Poly.1':1,'Contact.1':2,'Metal1.1':1,'Metal1.2':1}
    for svg in (ROOT/'assets').rglob('*.svg'):
        ET.parse(svg)
    # Every bundled family is mentioned in the atlas + expanded cell chapters.
    cdl = (ROOT/'examples/FreePDK45/NangateOpenCellLibrary.cdl').read_text()
    names = re.findall(r'^\.SUBCKT\s+(\S+)',cdl,re.M|re.I)
    families = {re.sub(r'_X\d+$','',name) for name in names}
    atlas = '\n'.join((ROOT/name).read_text() for name,*_ in BOOK if name.startswith('cells-') or name=='chapter9.html')
    assert len(names) == 135 and len(families) == 51
    for family in families:
        assert family in atlas, family
    summary = {'book_chapters':31,'appendices':1,'source_parser_tests':6,'simulation_points':9,'nldm_values':36,'liberty_parser':'passed','interpolation_ns':interpolation,'invalid_stimulus':'no measured cell_fall, failure log retained','drc_markers':categories,'cdl_cells':len(names),'cdl_families_mentioned':len(families),'scope':'teaching tests, not full generation or signoff'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'logs.json').write_text(json.dumps(logs,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    print(f'PASS. Evidence retained in {out}')


if __name__ == '__main__':
    main()
