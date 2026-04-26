import sys
from pathlib import Path

# Make the cli/ directory importable from tests
sys.path.insert(0, str(Path(__file__).parent.parent))
