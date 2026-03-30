import sys
from pathlib import Path

# Add src directory to path so tests can import the modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "sonarqube_mcp"))
