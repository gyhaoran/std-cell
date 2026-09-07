"""Patch/test a COPY of real LibreCell net_util.py. Never edits upstream.

Run with a Python environment that can import klayout.db and networkx.
The explicit model map is a local parser experiment, not a full tech API port.
"""
import argparse
import difflib
import importlib.util
import json
from pathlib import Path
import sys
import unittest


def module_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--librecell-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    root, out = args.librecell_root.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        p.error('output must be empty')
    sys.path[:0] = [str(root/'librecell-layout'), str(root/'librecell-common')]
    from lclayout.data_types import ChannelType
    source = root/'librecell-common/lccommon/net_util.py'
    old = source.read_text()
    signature = 'force_lowercase: bool = False) -> Tuple[List[Transistor], Set[str]]:'
    old_rule = "        if s.lower().startswith('n'):\n            return ChannelType.NMOS\n        return ChannelType.PMOS"
    new_rule = '''        mapping = model_channel_types
        if mapping is None:
            mapping = {'nmos': ChannelType.NMOS, 'pmos': ChannelType.PMOS}
        normalized = {name.lower(): kind for name, kind in mapping.items()}
        if s.lower() not in normalized:
            raise ValueError(f"Unknown MOS model: {s}; supply model_channel_types")
        kind = normalized[s.lower()]
        if kind not in (ChannelType.NMOS, ChannelType.PMOS):
            raise ValueError(f"Invalid channel type for MOS model: {s}")
        return kind'''
    if old.count(signature) != 1 or old.count(old_rule) != 1:
        p.error('upstream differs from expected source; inspect it before adapting this patch')
    new = old.replace(signature, 'force_lowercase: bool = False, model_channel_types=None) -> Tuple[List[Transistor], Set[str]]:').replace(old_rule, new_rule)
    changed = out/'net_util_patched.py'
    changed.write_text(new)
    (out/'model-map.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile='a/librecell-common/lccommon/net_util.py', tofile='b/librecell-common/lccommon/net_util.py')))
    baseline = module_from(source, 'tutorial_baseline')
    patched = module_from(changed, 'tutorial_patched')

    def parse(module, model='NMOS', length='0.050U', **kwargs):
        net = out/'case.sp'
        net.write_text(f'* teaching parser fixture\n.SUBCKT CHECK A Y VDD VSS\nM1 Y A VSS VSS {model} W=0.415U L={length}\n.ENDS\n')
        return module.load_transistor_netlist(str(net), 'CHECK', **kwargs)

    class ParserTests(unittest.TestCase):
        def test_known_nmos_and_pmos(self):
            for model, expected in [('nmos', ChannelType.NMOS), ('pmos', ChannelType.PMOS)]:
                self.assertEqual(parse(patched, model)[0][0].channel_type, expected)

        def test_unknown_fails_instead_of_becoming_pmos(self):
            self.assertEqual(parse(baseline, 'TYPO')[0][0].channel_type, ChannelType.PMOS)
            with self.assertRaisesRegex(ValueError, 'Unknown MOS model'):
                parse(patched, 'TYPO')

        def test_explicit_foundry_style_name(self):
            self.assertEqual(parse(baseline, 'CORE_NFET')[0][0].channel_type, ChannelType.PMOS)
            result = parse(patched, 'CORE_NFET', model_channel_types={'core_nfet': ChannelType.NMOS})
            self.assertEqual(result[0][0].channel_type, ChannelType.NMOS)

        def test_invalid_mapping_value(self):
            with self.assertRaisesRegex(ValueError, 'Invalid channel type'):
                parse(patched, model_channel_types={'nmos': 'n'})

        def test_width_unit_and_port_case(self):
            devices, pins = parse(patched, force_lowercase=True)
            self.assertAlmostEqual(devices[0].channel_width, .415e-6, delta=1e-15)
            self.assertEqual(pins, {'a', 'y', 'vdd', 'vss'})

        def test_length_is_not_stored_by_original_parser(self):
            short = parse(baseline, length='0.050U')[0][0]
            long = parse(baseline, length='0.100U')[0][0]
            self.assertEqual(vars(short), vars(long))

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ParserTests))
    (out/'result.json').write_text(json.dumps({'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'upstream_modified': False}, indent=2)+'\n')
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f'PASS: real parser before/after, patch and evidence in {out}')


if __name__ == '__main__':
    main()
