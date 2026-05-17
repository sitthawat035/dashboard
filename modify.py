import os
filepath = 'frontend/src/App.tsx'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'import AgentCard from' in line or 'import AgentCard' in line:
        lines[i] = "import AgentPage from './pages/AgentPage';\n"
        break

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if 'activeTab === \'agents\'' in line:
        start_idx = i
        break

if start_idx != -1:
    count = 0
    for i in range(start_idx, len(lines)):
        if '{' in lines[i]: count += lines[i].count('{')
        if '}' in lines[i]: count -= lines[i].count('}')
        if count == 0 and i > start_idx:
            end_idx = i
            break

if start_idx != -1 and end_idx != -1:
    new_content = """          {activeTab === 'agents' && (
            <AgentPage
              agents={agents}
              selectedAgent={selectedAgent}
              setSelectedAgent={setSelectedAgent}
              logData={logData}
              logTab={logTab}
              setLogTab={setLogTab}
              stdoutSubTab={stdoutSubTab}
              setStdoutSubTab={setStdoutSubTab}
              control={control}
              watchGwLog={watchGwLog}
              chatSessions={chatSessions}
              setChatSessions={setChatSessions}
              chatInputs={chatInputs}
              setChatInputs={setChatInputs}
              subagentLogs={subagentLogs}
            />
          )}
"""
    lines = lines[:start_idx] + [new_content] + lines[end_idx+1:]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Updated App.tsx imports and TSX rendering for AgentPage.")
else:
    print("Failed to find agent rendering block")
