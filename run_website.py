"""Start Streamlit and its tender monitor, including before the first browser session."""
from pathlib import Path
import sys


if __name__ == '__main__':
    from integrated_tenders.automatic import get_process_monitor
    from streamlit.web import cli

    monitor = get_process_monitor()
    sys.argv = ['streamlit', 'run', str(Path(__file__).with_name('streamlit_app.py')), *sys.argv[1:]]
    try:
        cli.main()
    finally:
        monitor.stop()
