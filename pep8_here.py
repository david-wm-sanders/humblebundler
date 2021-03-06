import subprocess
from pathlib import Path


# Run pep8 --exclude=venv --show-source .
p = Path(__file__).parent / Path(".")
subprocess.run(["pep8", "--exclude=venv", "--show-source", str(p)])
