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
    logs['concepts'] = run([sys.executable,'examples/learning/concept_checks.py'])
    logs['source'] = run([sys.executable,'examples/learning/source_lab.py','--librecell-root','/home/jasper/code/github/librecell','--output',str(out/'source')])
    logs['geometry'] = run([sys.executable,'examples/learning/geometry_lab.py','--output',str(out/'geometry')])
    logs['simulation'] = run([sys.executable,'examples/learning/characterize.py','--output',str(out/'simulation')])
    tg_out = out/'transmission-gates'
    logs['transmission_gates'] = run([sys.executable,'examples/learning/transmission_gate_lab.py','--output',str(tg_out)])
    tg_results = json.loads((tg_out/'measurements.json').read_text())
    assert set(tg_results) == {'pass_levels','isolation','mux','latch'}
    assert sum(map(len,tg_results.values())) == 25
    for case in tg_results.values():
        for record in case.values():
            value = record['voltage_V']
            low, high = record['accepted_range_V']
            assert math.isfinite(value) and low <= value <= high
    for s in (0,1):
        for a in (0,1):
            for b in (0,1):
                assert abs(tg_results['mux'][f'z_{s}{a}{b}']['voltage_V']-1.8*(b if s else a)) < 0.01
    for svg in tg_out.glob('*.svg'):
        ET.parse(svg)
    for svg in (ROOT/'examples/learning/tg-reference').glob('*.svg'):
        ET.parse(svg)
    # Safety negative case: rerunning into prior evidence must fail without edits.
    before = {p.relative_to(tg_out):p.read_bytes() for p in tg_out.rglob('*') if p.is_file()}
    refused = subprocess.run([sys.executable,'examples/learning/transmission_gate_lab.py','--output',str(tg_out)],cwd=ROOT,text=True,capture_output=True)
    assert refused.returncode != 0 and 'refusing to overwrite' in refused.stderr
    after = {p.relative_to(tg_out):p.read_bytes() for p in tg_out.rglob('*') if p.is_file()}
    assert before == after
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
    off_center = sum(w*values[r,c] for w,r,c in [(0.15,0,0),(0.60,0,1),(0.05,1,0),(0.20,1,1)])
    assert abs(off_center - 0.027822983) < 1e-7
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
    summary = {'book_chapters':sum(name != 'appendix.html' for name,*_ in BOOK),'appendices':1,'source_parser_tests':6,'simulation_points':9,'nldm_values':36,'tg_cases':len(tg_results),'tg_voltage_checks':sum(map(len,tg_results.values())),'tg_overwrite_refusal':'passed, prior evidence unchanged','liberty_parser':'passed','interpolation_ns':interpolation,'invalid_stimulus':'no measured cell_fall, failure log retained','drc_markers':categories,'cdl_cells':len(names),'cdl_families_mentioned':len(families),'scope':'teaching tests, not full generation or signoff'}
    summary.update({'cdl_concept_cases':16, 'off_center_interpolation_ns':off_center})
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'logs.json').write_text(json.dumps(logs,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    print(f'PASS. Evidence retained in {out}')


if __name__ == '__main__':
    main()
