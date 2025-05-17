import subprocess
import sys


def run_coverage():
    # Ensure coverage is installed
    try:
        import coverage
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "coverage"])

    # Run tests with coverage
    subprocess.check_call([
        sys.executable, "-m", "coverage", "run", "-m", "unittest", "discover", "."
    ])

    # Generate and display coverage report
    subprocess.check_call([
        sys.executable, "-m", "coverage", "report", "-m",
        "../dto/project.py", "../managers/blender_manager.py", "../managers/config_manager.py", "../util/utils.py"
    ])


if __name__ == "__main__":
    run_coverage()
