from pathlib import Path
import re

files = [
    "actool_linux/facet_hash_lookup.py",
    "actool_linux/nextgen/facet_hash_lookup.py",
    "actool_linux/research/facet_hash_lookup.py"
]

for fpath in files:
    with open(fpath, "r") as f:
        content = f.read()
    
    if "nextgen" in fpath or "research" in fpath:
        content = re.sub(r"Path\(__file__\)\.parent\.parent\.parent / 'facet_hash", r"Path(__file__).resolve().parent.parent / 'data' / 'facet_hash", content)
    else:
        content = re.sub(r"Path\(__file__\)\.parent\.parent\.parent / 'facet_hash", r"Path(__file__).resolve().parent / 'data' / 'facet_hash", content)

    with open(fpath, "w") as f:
        f.write(content)
