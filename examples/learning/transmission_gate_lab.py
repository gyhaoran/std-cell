"""Four reproducible transmission-gate lessons, using ngspice and the stdlib.

Uses intentionally simple Level-1 models, not a PDK or signoff result.
Writes decks, raw waveforms, logs, measured voltages and SVGs to a NEW directory.
No third-party Python packages required. Refuses to overwrite prior evidence.
"""
import argparse
import hashlib
from html import escape
import json
import math
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
COLORS = ['#2563eb', '#d97706', '#8b5cf6', '#059669', '#dc2626']


def pwl(bits, step=3):
    """Each bit is stable until the next step, with a 50 ps linear edge."""
    points = [f'0 {bits[0]*1.8:g}']
    for i in range(1, len(bits)):
        points.extend([f'{i*step:g}n {bits[i-1]*1.8:g}',
                       f'{i*step+0.05:g}n {bits[i]*1.8:g}'])
    points.append(f'{len(bits)*step:g}n {bits[-1]*1.8:g}')
    return 'PWL(' + ' '.join(points) + ')'


def cases():
    states = [(s, a, b) for s in (0, 1) for a in (0, 1) for b in (0, 1)]
    return {
        'pass_levels': {
            'title': 'Single MOS versus CMOS transmission gate', 'stop': 14,
            'circuit': '''VIN DIN 0 PULSE(0 1.8 2n 50p 50p 6n 20n)
MN YN VDD DIN 0 N_EDU W=1u L=0.18u
MP YP 0 DIN VDD P_EDU W=2u L=0.18u
XT DIN YTG VDD 0 VDD 0 EDU_TG
* Reverse test: drive the second signal port, observe the first.
XR YREV DIN VDD 0 VDD 0 EDU_TG
CN YN 0 20f
CP YP 0 20f
CT YTG 0 20f
CR YREV 0 20f''',
            'panels': [('v(din)', 'Input DIN'), ('v(yn)', 'NMOS only'),
                       ('v(yp)', 'PMOS only'), ('v(ytg)', 'TG X to Y'),
                       ('v(yrev)', 'TG Y to X')],
            'checks': [('n_high', 'yn', 7, 1.25, 1.45),
                       ('p_high', 'yp', 7, 1.79, 1.81),
                       ('tg_high', 'ytg', 7, 1.79, 1.81),
                       ('rev_high', 'yrev', 7, 1.79, 1.81),
                       ('n_low', 'yn', 13, -0.01, 0.01),
                       ('p_low', 'yp', 13, 0.35, 0.55),
                       ('tg_low', 'ytg', 13, -0.01, 0.01),
                       ('rev_low', 'yrev', 13, -0.01, 0.01)],
        },
        'isolation': {
            'title': 'Off-state isolation: idealized storage versus explicit leakage', 'stop': 14,
            'circuit': '''VIN DIN 0 PWL(0 0 2n 0 2.05n 1.8 8n 1.8 8.05n 0 14n 0)
VEN EN 0 PWL(0 1.8 5n 1.8 5.05n 0 10n 0 10.05n 1.8 14n 1.8)
XI EN ENB VDD 0 EDU_INV
XF DIN YFLOAT EN ENB VDD 0 EDU_TG
XL DIN YLEAK EN ENB VDD 0 EDU_TG
CF YFLOAT 0 20f
CL YLEAK 0 20f
* Deliberate teaching leakage path; NOT a fitted MOS off-leakage model.
RLEAK YLEAK 0 1meg''',
            'panels': [('v(din)', 'Input DIN'), ('v(en)', 'Enable EN'),
                       ('v(yfloat)', 'TG + 20 fF (no explicit leakage resistor)'),
                       ('v(yleak)', 'TG + 20 fF + 1 megohm to VSS')],
            'checks': [('float_hold', 'yfloat', 9, 1.75, 1.85),
                       ('leaky_hold', 'yleak', 9, 1.35, 1.6),
                       ('float_reopen', 'yfloat', 12, -0.01, 0.01),
                       ('leaky_reopen', 'yleak', 12, -0.01, 0.01)],
        },
        'mux': {
            'title': 'EDU_MUX2: all eight (S, A, B) combinations', 'stop': 24,
            'circuit': '\n'.join([
                f'V{pin} {pin} 0 {pwl([s[i] for s in states])}'
                for i, pin in enumerate(['S', 'A', 'B'])]) + '''
XU A B S Z VDD 0 EDU_MUX2
CL Z 0 20f''',
            'panels': [('v(s)', 'Select S'), ('v(a)', 'Data A'),
                       ('v(b)', 'Data B'), ('v(z)', 'Output Z = S ? B : A')],
            'checks': [(f'z_{s}{a}{b}', 'z', i*3+2,
                        (b if s else a)*1.8-0.01, (b if s else a)*1.8+0.01)
                       for i, (s, a, b) in enumerate(states)],
        },
        'latch': {
            'title': 'EDU_LATCH: transparent high, static feedback hold low', 'stop': 14,
            'circuit': '''VD D 0 PWL(0 0 2n 0 2.05n 1.8 8n 1.8 8.05n 0 14n 0)
VG G 0 PWL(0 1.8 5n 1.8 5.05n 0 11n 0 11.05n 1.8 14n 1.8)
XU D G Q VDD 0 EDU_LATCH
CL Q 0 20f''',
            'panels': [('v(d)', 'Data D'), ('v(g)', 'Gate G'),
                       ('v(q)', 'Output Q')],
            'checks': [('q_initial', 'q', 1, -0.01, 0.01),
                       ('q_follow', 'q', 4, 1.79, 1.81),
                       ('q_hold_before', 'q', 7, 1.79, 1.81),
                       ('q_hold_after', 'q', 10, 1.79, 1.81),
                       ('q_reopen', 'q', 13, -0.01, 0.01)],
        },
    }


def deck(case):
    measurements = '\n'.join(
        f'.measure tran {name} FIND v({node}) AT={time:g}n'
        for name, node, time, low, high in case['checks'])
    vectors = ' '.join(vector for vector, label in case['panels'])
    return f'''* {case['title']}
.include "{HERE / 'edu_inv.sp'}"
.include "{HERE / 'edu_tg.sp'}"
VDD VDD 0 1.8
{case['circuit']}
.temp 25
.tran 5p {case['stop']}n
{measurements}
.control
run
wrdata waveform.dat {vectors}
quit
.endc
.end
'''


def wave_svg(case, rows):
    """Code-native vector plots, one readable trace per strip; raw data retained."""
    width, left, right, top, strip = 1100, 90, 1060, 72, 155
    height = top + strip*len(case['panels']) + 40
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
             f'<title>{escape(case["title"])}</title>',
             '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="sans-serif" font-size="21" fill="#16243a">',
             f'<text x="30" y="32">{escape(case["title"])}</text>',
             '<text x="30" y="57" font-size="17">ngspice · educational Level-1 model · VDD = 1.8 V · CL = 20 fF</text>']
    # wrdata emits (time,value) for each vector unless wr_singlescale is set.
    for i, (vector, label) in enumerate(case['panels']):
        base = top+i*strip+35
        parts.append(f'<text x="{left}" y="{base-15}">{escape(label)}</text>')
        for voltage in [0, 0.9, 1.8]:
            y = base+90-voltage/1.8*90
            parts.extend([f'<path d="M{left} {y}H{right}" stroke="#dbe3ed"/>',
                          f'<text x="15" y="{y+6}" font-size="17">{voltage:g} V</text>'])
        for tick in range(0, case['stop']+1, 2):
            x = left+tick/case['stop']*(right-left)
            parts.append(f'<path d="M{x:.2f} {base}v90" stroke="#edf0f5"/>')
            if i == len(case['panels'])-1:
                parts.append(f'<text x="{x:.2f}" y="{base+115}" text-anchor="middle" font-size="17">{tick}</text>')
        points = ' '.join(f'{left+r[0]*1e9/case["stop"]*(right-left):.2f},{base+90-r[2*i+1]/1.8*90:.2f}' for r in rows)
        parts.append(f'<polyline points="{points}" fill="none" stroke="{COLORS[i]}" stroke-width="2.7" stroke-linejoin="round"/>')
    parts.append(f'<text x="{right}" y="{height-9}" text-anchor="end" font-size="19">Time (ns)</text></g></svg>')
    return '\n'.join(parts)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error('Output must be a new or empty directory; refusing to overwrite evidence.')
    simulator = shutil.which('ngspice')
    if not simulator:
        parser.error('ngspice is required; no simulation has been run.')
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, case in cases().items():
        folder = out/name
        folder.mkdir()
        (folder/'test.sp').write_text(deck(case))
        run = subprocess.run([simulator, '-b', '-o', 'run.log', 'test.sp'],
                             cwd=folder, capture_output=True, text=True, timeout=60)
        log = (folder/'run.log').read_text() if (folder/'run.log').exists() else ''
        if run.returncode or not (folder/'waveform.dat').exists():
            raise RuntimeError(f'{name}: ngspice failed; inspect {folder}\n{run.stderr}\n{log}')
        results[name] = {}
        for measure, node, time, low, high in case['checks']:
            match = re.search(rf'^\s*{re.escape(measure)}\s*=\s*([-+\deE.]+)', log, re.M)
            if not match:
                raise RuntimeError(f'{name}: missing measurement {measure}; inspect {folder}/run.log')
            value = float(match[1])
            if not math.isfinite(value) or not low <= value <= high:
                raise RuntimeError(f'{name}/{measure}: {value} V outside [{low}, {high}] V')
            results[name][measure] = {'voltage_V': value, 'time_ns': time,
                                      'accepted_range_V': [low, high]}
        rows = [[float(v) for v in line.split()]
                for line in (folder/'waveform.dat').read_text().splitlines() if line.strip()]
        if not rows or any(len(r) != 2*len(case['panels']) or not all(map(math.isfinite, r)) for r in rows):
            raise RuntimeError(f'{name}: invalid waveform columns/data')
        (out/f'{name}.svg').write_text(wave_svg(case, rows))
        print(f'{name}: PASS ({len(case["checks"])} measured voltages)')
    version = subprocess.run([simulator, '--version'], capture_output=True, text=True, check=True)
    provenance = {'simulator': version.stdout.strip(), 'simulator_path': simulator,
                  'source_sha256': {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                                    for name in ['edu_inv.sp', 'edu_tg.sp', Path(__file__).name]},
                  'scope': 'educational Level-1 transient checks; NOT PDK, PEX, power, timing characterization or signoff',
                  'cases': len(results), 'voltage_checks': sum(map(len, results.values()))}
    (out/'measurements.json').write_text(json.dumps(results, indent=2)+'\n')
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print(f'Evidence: {out}')


if __name__ == '__main__':
    main()
