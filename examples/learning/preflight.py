"""Read-only dependency report; does not install packages or alter environment."""
import importlib.metadata as metadata
import importlib.util
import json
import platform
import shutil
import sys

packages = {}
for name in ['klayout','networkx','numpy','scipy','PyQt5','z3-solver','pysmt','liberty-parser']:
    try:
        packages[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        packages[name] = None
commands = {name: shutil.which(name) for name in ['ngspice','klayout','lclayout','lctime']}
missing = [name for name in ['z3','pysmt'] if importlib.util.find_spec(name) is None]
print(json.dumps({'python': platform.python_version(), 'executable': sys.executable, 'packages': packages, 'commands': commands, 'known_layout_import_blockers': missing, 'note': 'finding an executable does not prove it starts or completes a run'}, indent=2))
