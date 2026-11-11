"""Preview launcher: local Python 3.12 + the packages already in .venv (its own interpreter path is from another PC)."""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.venv' / 'Lib' / 'site-packages'))
sys.path.insert(0, str(ROOT))
sys.argv = [str(ROOT / 'run_website.py'), '--server.port', '8765']
runpy.run_path(str(ROOT / 'run_website.py'), run_name='__main__')
