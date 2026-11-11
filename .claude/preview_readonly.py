"""Review-only preview: same site as preview_server.py, but never commits, pushes, rebuilds or collects."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ['RECONSTRUCTION_AUTO_UPDATE'] = '0'
sys.path.insert(0, str(ROOT / '.venv' / 'Lib' / 'site-packages'))
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from streamlit.web import cli

sys.argv = ['streamlit', 'run', str(ROOT / 'streamlit_app.py'), '--server.port', '8767',
            '--server.headless', 'true', '--server.runOnSave', 'false']
cli.main()
