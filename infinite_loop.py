import requests
import time
import sys

# ==========================================
# 🔄 The Infinite Agent Loop (Chaos Engine) 🔄
# ==========================================

# 1. ตั้งค่า Agent ทั้ง 3 ตัว (อิงจากพอร์ตและ Token จริงของเรา)
AGENTS = {
    "ace": {"port": 18889, "token": "c8781be6da7abfe318241480c884ec50865d7949366224e2", "color": "\033[96m", "name": "🚀 Ace (Analyst)"},
    "ameri": {"port": 18890, "token": "6cb4ad62e41987e84f4daba2e8643e76191939e6e6a52b79", "color": "\033[95m", "name": "🧠 Ameri (Coder)"},
    "pudding": {"port": 18891, "token": "e48a1de7c7d47651cd6846b45c7d4023c7167c735bbe407b", "color": "\033[93m", "name": "🍮 Pudding (Reviewer)"}
}

ORDER = ["ace", "ameri", "pudding"]

def print_colored(text, color_code):
    print(f"{color_code}{text}\033[0m")

def ask_agent(agent_key, prompt):
    agent = AGENTS[agent_key]
    print_colored(f"\n[{agent['name']}] กำลังคิด...", agent['color'])
    
    # ส่งข้อความไปหา OpenClaw Gateway ผ่าน API
    # (หาก OpenClaw รองรับ /v1/chat/completions หรือ /message)
    try:
        # หมายเหตุ: Endpoint นี้อาจต้องปรับแก้ตามเวอร์ชันของ OpenClaw 
        # ปกติจะเป็น /v1/chat/completions แบบ OpenAI Compatible
        response = requests.post(
            f"http://127.0.0.1:{agent['port']}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {agent['token']}",
                "Content-Type": "application/json"
            },
            json={
                "model": "auto", 
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150 # บังคับให้ตอบสั้นๆ จะได้ไม่รอนาน
            },
            timeout=60
        )
        
        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content']
            return reply
        else:
            return f"(Error: {response.status_code}) สงสัยหลับอยู่..."
    except Exception as e:
        return f"(Connection Error) {str(e)}"

# 2. เริ่มต้น Loop อนันต์!
def start_chaos(initial_prompt):
    print_colored("==========================================", "\033[91m")
    print_colored(" ☢️ INITIATING AUTONOMOUS AGENT LOOP ☢️ ", "\033[91m")
    print_colored("==========================================", "\033[91m")
    
    current_prompt = initial_prompt
    loop_count = 1
    
    while True:
        print_colored(f"\n--- 🔄 Loop Cycle #{loop_count} ---", "\033[92m")
        
        for agent_key in ORDER:
            # เพิ่ม Instruction บังคับให้มันคุยต่อยอดกัน
            instruction = f"Context from previous agent:\n\n'{current_prompt}'\n\nYour task: Reply to this, keep it short (max 2 sentences), and ask a follow up question for the next agent."
            
            reply = ask_agent(agent_key, instruction)
            print_colored(f"> {reply}", "\033[97m")
            
            # ส่งคำตอบของตัวนี้ ไปเป็นคำถามของตัวถัดไป
            current_prompt = reply
            time.sleep(2) # ให้หายใจแป๊บ
            
        loop_count += 1
        time.sleep(5) # พักเครื่องระหว่างรอบ

if __name__ == "__main__":
    initial_idea = "เรากำลังจะสร้างอาณาจักร AI ครองโลก เริ่มต้นยังไงดี?"
    try:
        start_chaos(initial_idea)
    except KeyboardInterrupt:
        print_colored("\n\n🛑 EMERGENCY STOP: ปิดระบบ Loop แล้ว!", "\033[91m")
