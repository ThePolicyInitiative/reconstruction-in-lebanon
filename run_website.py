"""Start Streamlit with its tender monitor and automatic updates, including before the first browser session."""
from pathlib import Path
import sys


if __name__ == '__main__':
    from auto_update import get_process_updater
    from integrated_tenders.automatic import get_process_monitor
    from streamlit.web import cli

    monitor = get_process_monitor()
    # The local launcher also publishes checked changes to GitHub.
    updater = get_process_updater(publish=True)
    sys.argv = ['streamlit', 'run', str(Path(__file__).with_name('streamlit_app.py')), *sys.argv[1:]]
    try:
        cli.main()
    finally:
        monitor.stop()
        updater.stop()
