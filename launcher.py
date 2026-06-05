import sys
import os
import subprocess
import threading
import webbrowser
import time
from pathlib import Path


def get_base_dir():
    # when running as EXE — PyInstaller unpacks to temp folder
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    # when running normally
    return Path(__file__).parent


def open_browser():
    # wait for Streamlit to start then open browser
    time.sleep(3)
    webbrowser.open("http://localhost:8501")


def run_streamlit():
    base_dir = get_base_dir()
    app_path = base_dir / "app.py"

    # find streamlit executable
    streamlit_cmd = [
        sys.executable,
        "-m", "streamlit",
        "run", str(app_path),
        "--server.port", "8501",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]

    subprocess.run(streamlit_cmd)


if __name__ == "__main__":
    # open browser in background thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    # run streamlit in main thread
    run_streamlit()