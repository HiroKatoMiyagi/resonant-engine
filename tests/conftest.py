"""
Root pytest configuration for all tests

Ensures project root is in Python path for all test modules.
"""

import sys
from pathlib import Path

# Add project root to path at start of tests
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
