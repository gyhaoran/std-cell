"""Check worked examples against bundled CDL and exact teaching arithmetic.

No file writes, no third-party dependencies. MOS are ideal on/off switches:
this checks Boolean rail connectivity, NOT analog stability, DRC, LVS or timing.
"""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import re


EXAMPLES_ROOT = Path(__file__).resolve().parents[1]
CDL = EXAMPLES_ROOT / 'FreePDK45/NangateOpenCellLibrary.cdl'


def devices(name):
    text = CDL.read_text()
    block = re.search(r'^\.SUBCKT\s+' + re.escape(name) + r'\s+[^\n]*\n(.*?)^\.ENDS',
                      text, re.M | re.S | re.I)
    assert block, name
    # name, D, G, S, B, model; original file is never modified.
    return [tuple(line.split()[:6]) for line in block[1].splitlines()
            if line.startswith('M')]


def reachable(graph, start):
    seen, pending = {start}, [start]
    while pending:
        node = pending.pop()
        for other in graph.get(node, ()):
            if other not in seen:
                seen.add(other)
                pending.append(other)
    return seen


def stable_rail_states(mos, inputs, output):
    """Enumerate internal gate levels; require each to be driven consistently.

    Floating *diffusion* nodes are permitted. Floating internal gate values are
    excluded, so this is intentionally limited to these static examples.
    """
    fixed = {'VDD': 1, 'VSS': 0, **inputs}
    gates = sorted({m[2] for m in mos} - fixed.keys())
    result = []
    for bits in product((0, 1), repeat=len(gates)):
        levels = {**fixed, **dict(zip(gates, bits))}
        graph = {}
        for name, drain, gate, source, body, model in mos:
            assert model in ('NMOS_VTL', 'PMOS_VTL'), (name, model)
            is_n = model == 'NMOS_VTL'
            assert body == ('VSS' if is_n else 'VDD')
            if levels[gate] == int(is_n):
                graph.setdefault(drain, set()).add(source)
                graph.setdefault(source, set()).add(drain)
        high, low = reachable(graph, 'VDD'), reachable(graph, 'VSS')
        if high & low:
            continue  # Both rails connected: not a valid static solution.
        if any(g not in (high if levels[g] else low) for g in gates):
            continue
        value = 1 if output in high else 0 if output in low else 'Z'
        result.append((levels, value))
    return result


def check_cdl():
    aoi = devices('AOI21_X1')
    assert len(aoi) == 6
    for a, b1, b2 in product((0, 1), repeat=3):
        states = stable_rail_states(aoi, {'A': a, 'B1': b1, 'B2': b2}, 'ZN')
        assert {value for _, value in states} == {int(not (a or b1 and b2))}

    tinv = devices('TINV_X1')
    assert len(tinv) == 6
    for en, data in product((0, 1), repeat=2):
        states = stable_rail_states(tinv, {'EN': en, 'I': data}, 'ZN')
        assert {value for _, value in states} == {'Z' if en else 1-data}
        assert all(levels['net_000'] == 1-en for levels, _ in states)

    latch = devices('DLH_X1')
    groups = [
        {'M_i_0', 'M_i_48'}, {'M_i_7', 'M_i_55'},
        {'M_i_13', 'M_i_18', 'M_i_61', 'M_i_66'},
        {'M_i_34', 'M_i_82'},
        {'M_i_24', 'M_i_28', 'M_i_72', 'M_i_76'},
        {'M_i_41_11', 'M_i_89_4'},
    ]
    assert len(latch) == sum(map(len, groups)) == 16
    assert set.union(*groups) == {m[0] for m in latch}
    for enable, data in product((0, 1), repeat=2):
        states = stable_rail_states(latch, {'G': enable, 'D': data}, 'Q')
        assert {value for _, value in states} == ({data} if enable else {0, 1})
        for levels, value in states:
            assert levels['net_000'] == 1-enable
            assert levels['net_001'] == enable
            assert levels['net_003'] == 1-value
            assert levels['net_005'] == value
    return 8 + 4 + 4


def check_numbers():
    # Chapter 10: DBU, area, boundary/grid and minimum-area pad.
    dbu_um = F('0.001')
    assert F('0.075') / dbu_um == 75
    assert F('0.01') / dbu_um**2 == 10000
    assert F('0.415') / dbu_um == 415
    assert 103 % 5 != 0 and 100 % 5 == 0
    assert (120 - 40 // 2, 120 + 40 // 2) == (100, 140)
    assert 60 + 2*15 == 90
    assert F('0.09') * F('0.135') == F('0.01215')
    assert F('0.09') * F('0.13') < F('0.012')
    # Chapter 11/13: first-order RC and charge/current intuition only.
    assert F('0.693')*2000*F('1e-14') == F('13.86e-12')
    assert F('0.693')*2000*F('1.5e-14') == F('20.79e-12')
    assert F('20e-15')*1/F('100e-6') == F('200e-12')
    # Chapter 16: every full-adder row plus 4-bit ripple carry.
    for a, b, ci in product((0, 1), repeat=3):
        s, co = a ^ b ^ ci, int(a+b+ci >= 2)
        assert a+b+ci == s + 2*co
    for ci, expected in ((0, 15), (1, 16)):
        result = 0
        for bit in range(4):
            s, ci = 1 ^ 0 ^ ci, ci  # All stages propagate: A=1, B=0.
            result |= s << bit
        result |= ci << 4
        assert result == expected
    # Chapters 18/23/29: time windows, via-center window, repair/neighbor.
    assert F(10)-F('0.2') == F('9.8')
    assert F(10)+F('0.1') == F('10.1')
    margin = 40//2 + 20
    window = (100+margin, 200-margin)
    assert window == (140, 160)
    assert not [x for x in range(0, 301, 100) if window[0] <= x <= window[1]]
    assert [x for x in range(50, 301, 100) if window[0] <= x <= window[1]] == [150]
    assert 100-30-30 == 40 < 50
    assert 65+2*35 == 135
    assert 250-170 == 80 and 250-200 == 50 < 60
    # Chapter 31: asymmetric bilinear weights from stored reference values.
    d00, d01, d10, d11 = map(F, ('0.01192294', '0.02560823', '0.02241280', '0.04774482'))
    u, v = F(35-20, 80-20), F(17-5, 20-5)
    weights = ((1-u)*(1-v), (1-u)*v, u*(1-v), u*v)
    assert weights == tuple(map(F, ('0.15', '0.60', '0.05', '0.20')))
    assert sum(weights) == 1
    direct = sum(w*d for w, d in zip(weights, (d00, d01, d10, d11)))
    along_rows = (1-u)*((1-v)*d00+v*d01) + u*((1-v)*d10+v*d11)
    assert direct == along_rows == F('0.027822983')


def main():
    count = check_cdl()
    check_numbers()
    print(f'PASS: {count} CDL input cases (AOI21, TINV, DLH), six DLH groups; worked arithmetic')
    print('Scope: ideal static rail connectivity and teaching arithmetic, NOT SPICE/LVS/DRC/PEX signoff')


if __name__ == '__main__':
    main()
