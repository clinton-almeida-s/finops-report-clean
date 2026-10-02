"""
GCP Cloud Cost Optimizer - Launcher
Properly starts the Streamlit application
"""
import subprocess
import sys
import os


def main():
    """Launch Streamlit app with proper command."""
    script_path = os.path.dirname(os.path.abspath(__file__))
    app_file = os.path.join(script_path, "app.py")

    print("=" * 60)
    print("GCP Cloud Cost Optimizer")
    print("=" * 60)
    print(f"\nStarting dashboard at http://localhost:8501")
    print("Press Ctrl+C to stop\n")
    print("=" * 60)

    # Run streamlit with proper command
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", app_file,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ], check=True)


if __name__ == "__main__":
    main()