import os
import re
import sys

sys.path.insert(0, '.')
from api.config import AGENTS

for key, agent in AGENTS.items():
    cmd_file = agent.get('gateway_cmd')
    if cmd_file and os.path.exists(cmd_file):
        with open(cmd_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        name = agent.get('name', key)
        # Replace spaces with underscores for the task name to avoid quoting issues inside openclaw JS
        task_name = f'OpenClaw_Gateway_{name}'.replace(' ', '_')
        
        content = re.sub(
            r'^set "OPENCLAW_WINDOWS_TASK_NAME=.*?"', 
            f'set "OPENCLAW_WINDOWS_TASK_NAME={task_name}"', 
            content, flags=re.MULTILINE
        )
        
        with open(cmd_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Fixed {cmd_file} for {key} with {task_name}')
