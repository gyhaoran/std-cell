"""Reproducible teaching NLDM, Python standard library + ngspice.

Writes only into --output (use a fresh directory). It is not a production
characterizer: no PEX, power, input capacitance or sequential constraints.
PULSE ramp is 0--100%; the Liberty index is the measured 20--80% duration.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
NAMES = ('cell_rise', 'cell_fall', 'rise_transition', 'fall_transition')
SLEWS_PS = (20, 80, 200)
LOADS_FF = (5, 20, 50)


def deck(slew_ps, load_ff):
    # Linear PULSE: t_20--80 = 0.6 * t_0--100.
    ramp_ps = slew_ps / 0.6
    return f'''EDU_INV teaching characterization
.include "{HERE / 'edu_inv.sp'}"
VDD VDD 0 1.8
VA A 0 PULSE(0 1.8 2n {ramp_ps:.12g}p {ramp_ps:.12g}p 8n 20n)
XU A Y VDD 0 EDU_INV
CL Y 0 {load_ff}f
.tran 2p 18n
.measure tran cell_fall TRIG v(A) VAL=0.9 RISE=1 TARG v(Y) VAL=0.9 FALL=1
.measure tran cell_rise TRIG v(A) VAL=0.9 FALL=1 TARG v(Y) VAL=0.9 RISE=1
.measure tran rise_transition TRIG v(Y) VAL=0.36 RISE=1 TARG v(Y) VAL=1.44 RISE=1
.measure tran fall_transition TRIG v(Y) VAL=1.44 FALL=1 TARG v(Y) VAL=0.36 FALL=1
.measure tran input_slew TRIG v(A) VAL=0.36 RISE=1 TARG v(A) VAL=1.44 RISE=1
.control
run
wrdata waveform.dat v(A) v(Y)
quit
.endc
.end
'''


def wave_svg(path, target):
    data = [list(map(float, line.split())) for line in path.read_text().splitlines()]
    # Zoom to the first falling output; include the entire first input ramp.
    rows = [r for r in data if 1.8e-9 <= r[0] <= 3.1e-9][::3]
    def points(col):
        return ' '.join(f'{90+(r[0]*1e9-1.8)/1.3*980:.2f},{330-r[col]/1.8*235:.2f}' for r in rows)
    target.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 440" role="img" aria-labelledby="t">
<title id="t">ngspice 实测波形：输入上升，反相器输出下降</title><rect width="1160" height="440" fill="white"/>
<g font-family="sans-serif" font-size="20" fill="#172033"><text x="40" y="36">EDU_INV · slew 80 ps（20–80%），负载 20 fF，VDD 1.8 V</text>
<path d="M90 75 V330 H1090" fill="none" stroke="#475467"/>
<path d="M90 212.5 H1090" stroke="#98a2b3" stroke-dasharray="7 5"/>
<text x="18" y="102">1.8 V</text><text x="18" y="219">0.9 V</text><text x="29" y="337">0 V</text>
<polyline points="{points(1)}" fill="none" stroke="#2457d6" stroke-width="3"/>
<polyline points="{points(3)}" fill="none" stroke="#c4320a" stroke-width="3"/>
<text x="90" y="367">1.8 ns</text><text x="1010" y="367">3.1 ns</text>
<text x="250" y="409" fill="#2457d6">A：输入</text><text x="470" y="409" fill="#c4320a">Y：输出</text><text x="665" y="409">虚线为 50% 测量阈值</text></g></svg>''', encoding='utf-8')


def liberty(results):
    tables = []
    for name in NAMES:
        rows = []
        for slew in SLEWS_PS:
            row = [results[f'{slew}ps_{load}ff'][name] * 1e9 for load in LOADS_FF]
            rows.append('"' + ', '.join(f'{v:.8g}' for v in row) + '"')
        tables.append(f'        {name} (delay_3x3) {{\n          values (' + ', \\\n                  '.join(rows) + ');\n        }')
    return '''/* EDUCATION ONLY: ideal Level-1 models, no PEX or signoff. */
library (EDU_TT) {
  delay_model : table_lookup;
  time_unit : "1ns";
  voltage_unit : "1V";
  current_unit : "1mA";
  capacitive_load_unit (1, pf);
  nom_voltage : 1.8;
  nom_temperature : 27;
  nom_process : 1;
  input_threshold_pct_rise : 50;
  input_threshold_pct_fall : 50;
  output_threshold_pct_rise : 50;
  output_threshold_pct_fall : 50;
  slew_lower_threshold_pct_rise : 20;
  slew_upper_threshold_pct_rise : 80;
  slew_lower_threshold_pct_fall : 20;
  slew_upper_threshold_pct_fall : 80;
  lu_table_template (delay_3x3) {
    variable_1 : input_net_transition;
    variable_2 : total_output_net_capacitance;
    index_1 ("0.02, 0.08, 0.2");
    index_2 ("0.005, 0.02, 0.05");
  }
  cell (EDU_INV) {
    pin (A) { direction : input; }
    pin (Y) {
      direction : output;
      function : "!A";
      max_capacitance : 0.05;
      timing () {
        related_pin : "A";
        timing_sense : negative_unate;
        timing_type : combinational;
''' + '\n'.join(tables) + '''
      }
    }
  }
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not shutil.which('ngspice'):
        parser.error('ngspice not found: install it before this experiment')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        parser.error('output must be empty; preserve previous evidence in its old directory')
    results = {}
    for slew in SLEWS_PS:
        for load in LOADS_FF:
            name = f'{slew}ps_{load}ff'
            case = out / name
            case.mkdir()
            (case / 'test.sp').write_text(deck(slew, load))
            run = subprocess.run(['ngspice', '-b', '-o', 'run.log', 'test.sp'], cwd=case, capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError(f'{name}: ngspice failed; inspect {case / "run.log"}')
            log = (case / 'run.log').read_text()
            values = {}
            for key in (*NAMES, 'input_slew'):
                match = re.search(rf'^\s*{key}\s*=\s*([\d.eE+-]+)', log, re.M)
                if not match:
                    raise RuntimeError(f'{name}: missing measurement {key}; no sentinel replacement allowed')
                value = float(match[1])
                if not 0 < value < 1e-6:
                    raise RuntimeError(f'{name}: invalid {key}={value}')
                values[key] = value
            assert abs(values['input_slew'] - slew*1e-12) < 1e-14
            results[name] = values
    (out / 'measurements.json').write_text(json.dumps(results, indent=2) + '\n')
    with (out / 'measurements.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['slew_ps', 'load_ff', *(n + '_ps' for n in NAMES)])
        for s in SLEWS_PS:
            for c in LOADS_FF:
                writer.writerow([s, c, *(results[f'{s}ps_{c}ff'][n]*1e12 for n in NAMES)])
    (out / 'edu_inv.lib').write_text(liberty(results))
    wave_svg(out / '80ps_20ff/waveform.dat', out / 'waveform.svg')
    version = subprocess.run(['ngspice', '--version'], capture_output=True, text=True).stdout
    (out / 'provenance.json').write_text(json.dumps({'simulator': version, 'model_sha256': hashlib.sha256((HERE/'edu_inv.sp').read_bytes()).hexdigest(), 'case_count': len(results), 'status': 'teaching measurement only'}, indent=2) + '\n')
    print(f'PASS: {len(results)} cases, 36 NLDM values, measured input slews; {out}')


if __name__ == '__main__':
    main()
