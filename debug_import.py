import sys
import os
print(f"CWD: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
sys.path.append(os.path.join(os.getcwd(), 'backend'))
for p in sys.path:
    print(p)

try:
    import app
    print(f"Imported app: {app}")
except ImportError as e:
    print(f"Error importing app: {e}")

try:
    import backend
    print(f"Imported backend: {backend}")
    import backend.app
    print(f"Imported backend.app: {backend.app}")
except ImportError as e:
    print(f"Error importing backend: {e}")

try:
    import context_assembler
    print(f"Imported context_assembler: {context_assembler}")
    import context_assembler.service
    print(f"Imported context_assembler.service: {context_assembler.service}")
except ImportError as e:
    print(f"Error importing context_assembler: {e}")

try:
    import bridge.memory.models
    print(f"Imported bridge.memory.models: {bridge.memory.models}")
except ImportError as e:
    print(f"Error importing bridge: {e}")
