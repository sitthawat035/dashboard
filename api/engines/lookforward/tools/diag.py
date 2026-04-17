"""Diagnostic script to verify common_shared imports work correctly."""
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

print('--- DIAGNOSTIC START ---')
print(f'Python Version: {sys.version}')

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
root_dir = project_root.parent

print(f'Project root: {project_root}')
print(f'Root dir: {root_dir}')

sys.path.insert(0, str(root_dir))

try:
    print('Testing imports from common_shared...')
    from common_shared.utils import setup_logger
    print('[OK] common_shared.utils')
    from common_shared.config import Config
    print('[OK] common_shared.config')
    from common_shared.ai_client import create_ai_client
    print('[OK] common_shared.ai_client')
    print('ALL IMPORTS SUCCESSFUL')
except Exception as e:
    print(f'[FAIL] {e}')
    import traceback
    traceback.print_exc()

print('--- DIAGNOSTIC END ---')
    import traceback
    traceback.print_exc()

print('--- DIAGNOSTIC END ---')

