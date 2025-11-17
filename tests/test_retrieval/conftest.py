"""
Retrieval Tests Configuration

Ensures proper Python path setup for retrieval tests.
"""

import sys
from pathlib import Path
import importlib

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Force reimport of retrieval package
if 'retrieval' in sys.modules:
    del sys.modules['retrieval']

# Now import the retrieval package to ensure it's available
import retrieval
