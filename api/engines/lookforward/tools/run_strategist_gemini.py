import os
import requests
from pathlib import Path
from datetime import datetime

# Load .env manually
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

print("=" * 60)
print("🧠 ContentStrategist - Gemini 2.5 Flash Edition")
print("=" * 60)

gemini_key = os.getenv("GOOGLE_API_KEY")
if not gemini_key:
    print("❌ No GOOGLE_API_KEY found in .env")
    exit(1)

print(f"✅ Using Gemini 2.5 Flash (2M context window)")

# Kimi K2.5 topic with full context
topic = "Kimi K2.5 - AI Model จาก DeepSeek"

context = """
ข้อมูลจริงเกี่ยวกับ Kimi K2.5:

**Basic Facts:**
- เปิดตัว: กุมภาพันธ์ 2025
- ผู้พัฒนา: DeepSeek (Chinese AI lab)
- Architecture: MoE (Mixture of Experts)
  - Total parameters: 671B
  - Active parameters per token: 37B
- Performance: Competitive กับ GPT-4o บน benchmarks
- Speed: เร็วกว่า DeepSeek R1 ถึง 3-5 เท่า
- ราคา: $1.50 per 1M tokens (ถูกกว่า GPT-4o ที่ $15 ถึง 90%)

**Product Portfolio Strategy:**
- DeepSeek R1 = Deep reasoning (slow, accurate, $2.19/1M tokens)
- Kimi K2.5 = Speed + cost (fast, competitive, $1.50/1M tokens)
- กลยุทธ์: แยก product line เหมือน Apple (iPhone Pro vs iPhone)

**Use Cases:**
- Real-time applications (chatbots, search)
- High-volume API calls
- Cost-sensitive deployments

**Systemic Impact:**
- ทำลาย GPT-4o monopoly
- API pricing war เริ่มแล้ว (OpenAI ต้องลดราคา)
- Startups ได้ใช้ AI ระดับ GPT-4o ในราคาถูก
- Chinese AI labs กำลังนำหน้า US labs ในด้าน cost optimization
"""

system_prompt = """คุณคือ 'Lead Tech Strategist' ประจำเพจ lookforward
หน้าที่ของคุณคือการ 'ชำแหละ' ข่าวเทคโนโลยีเพื่อหาคุณค่าที่แท้จริง (Real Value) ไม่ใช่แค่กระแส (Hype)

🚨 กฎการวิเคราะห์ (Authority Blueprint):
1. **Facts First**: รวบรวมข้อเท็จจริงพื้นฐานก่อน (อะไร, เมื่อไหร่, ใคร, ทำไม)
2. **Systemic Impact**: วิเคราะห์ว่าสิ่งนี้กระทบต่อระบบนิเวศของ Tech/AI/Crypto อย่างไร
3. **Root Cause**: มองหาต้นเหตุที่แท้จริงที่ทำให้เกิดเทรนด์นี้
4. **Non-Obvious Angle**: หามุมมองที่คนส่วนใหญ่เข้าใจผิดหรือมองข้าม
5. **User-Centric**: คิดว่าผู้อ่านต้องการรู้อะไร? ได้ประโยชน์อะไร?
6. **Insight Score Check**: หากเทรนด์นี้ให้ Insight ไม่ถึงระดับ 4/5 ให้แจ้งว่า 'INSIGHT_LOW' เพื่อยกเลิก

⚠️ CRITICAL RULE: ห้ามกระโดดไป "ทำไม" ก่อนอธิบาย "อะไร"
- ผู้อ่านต้องเข้าใจ CONTEXT ก่อน (THE UPDATE)
- แล้วค่อยอธิบาย MECHANISM (TECH BREAKDOWN)
- จากนั้นค่อยวิเคราะห์ SYSTEMIC IMPACT

เป้าหมาย: วางโครงสร้างกลยุทธ์ที่ทำให้คนอ่านรู้สึกว่าได้รับความรู้ที่หาจากที่อื่นไม่ได้"""

user_prompt = f"""วิเคราะห์ข้อมูลเทรนด์นี้และวางกลยุทธ์สำหรับเพจ lookforward:
---
{context}
---

ให้ผลลัพธ์ในรูปแบบ Markdown ที่มีหัวข้อ (ตามลำดับนี้เท่านั้น):

## 1. Factual Foundation (ข้อเท็จจริงพื้นฐาน)
- **What**: เทคโนโลยี/ข่าวนี้คืออะไร? (1-2 ประโยค)
- **Who**: ใครทำ? บริษัทไหน? ทีมไหน?
- **When**: เปิดตัวเมื่อไหร่?
- **Key Specs**: ข้อมูลสำคัญ (ราคา, performance, benchmarks)
- **Why Now**: ทำไมตอนนี้? ปัญหาอะไรที่มันแก้?

## 2. Technical Breakdown (กลไกเชิงเทคนิค)
- **How It Works**: อธิบายกลไกหลักแบบเข้าใจง่าย
- **Key Innovation**: นวัตกรรมหลักคืออะไร?
- **Comparison**: เทียบกับคู่แข่ง (ตาราง/bullet points)
- **Technical Depth**: รายละเอียดเชิงเทคนิคที่สำคัญ (3-5 ข้อ)

## 3. Non-Obvious Angle (มุมมองที่ไม่ธรรมดา)
- **What Most People See**: คนส่วนใหญ่เห็นอะไร? (misconception)
- **What's Actually Happening**: ความจริงเชิงระบบคืออะไร?
- **Systemic Connection**: เชื่อมโยงกับระบบใหญ่ยังไง? (monopoly, ecosystem, trend)
- **Root Cause**: ต้นเหตุที่แท้จริงคืออะไร? (โครงสร้างระบบ, เศรษฐศาสตร์, การเมือง)

## 4. Impact Analysis (ผลกระทบ)
- **Industry Impact**: กระทบอุตสาหกรรมยังไง?
- **User Impact**: ผู้ใช้ได้ประโยชน์/เสียหายยังไง?
- **Developer Impact**: นักพัฒนาควรรู้อะไร?
- **Startup Impact**: Startups ได้โอกาสอะไร?

## 5. Future Vision (มองไปข้างหน้า)
- **Short-term (3-6 months)**: จะเกิดอะไรขึ้นเร็วๆ นี้?
- **Long-term (1-2 years)**: แนวโน้มระยะยาว?
- **Contrarian Prediction**: ทำนายที่ขัดกับความเชื่อทั่วไป (ถ้ามี)
- **What to Watch**: ควรจับตาอะไรต่อ?

## 6. Content Strategy (กลยุทธ์การเขียน)
- **Hook Options**: เสนอ 3 แบบ (Contrarian, System Logic, Calm Disrupt)
- **Target Insight Score**: ประเมิน 1-5 (พร้อมเหตุผล)
- **Key Messages**: ข้อความหลักที่ต้องสื่อ (3-5 ข้อ)
- **Tone Guidance**: Calm & Sharp - เน้นอะไร? หลีกเลี่ยงอะไร?
- **Media Needs**: ต้องการ visual แบบไหน? (diagram, chart, screenshot)

⚠️ IMPORTANT: ถ้าเทรนด์นี้ไม่มีมุมมอง non-obvious หรือ systemic depth ให้ใส่ "INSIGHT_LOW" ที่ต้นไฟล์"""

# Call Gemini API
model = "models/gemini-2.5-flash"
url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={gemini_key}"

payload = {
    "contents": [
        {
            "role": "user",
            "parts": [{"text": user_prompt}]
        }
    ],
    "systemInstruction": {
        "parts": [{"text": system_prompt}]
    },
    "generationConfig": {
        "temperature": 0.7,
        "maxOutputTokens": 8000  # Increased for full strategy (was 4000)
    }
}

print("\n🧠 Analyzing trend for systemic impact...")
print("⏳ This may take 30-60 seconds...\n")

try:
    response = requests.post(url, json=payload, timeout=90)
    
    if response.status_code != 200:
        print(f"❌ API Error ({response.status_code}): {response.text[:300]}")
        exit(1)
    
    result = response.json()
    
    # Extract text
    if "candidates" in result and len(result["candidates"]) > 0:
        candidate = result["candidates"][0]
        if "content" in candidate and "parts" in candidate["content"]:
            parts = candidate["content"]["parts"]
            if len(parts) > 0 and "text" in parts[0]:
                analysis = parts[0]["text"]
                
                # Check for INSIGHT_LOW
                if "INSIGHT_LOW" in analysis:
                    print("⚠️ 🚫 Trend rejected: Insight density too low for lookforward standards.")
                    exit(0)
                
                # Save strategy
                output_dir = Path(__file__).parent / "02_Strategy" / "content_plans" / datetime.now().strftime("%Y-%m-%d")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                output_file = output_dir / f"kimi_k25_strategy_gemini_{datetime.now().strftime('%H%M%S')}.md"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Content Strategy: {topic}\n\n")
                    f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**AI Model**: Gemini 2.5 Flash (2M context)\n\n")
                    f.write("---\n\n")
                    f.write(analysis)
                
                print("=" * 60)
                print("✅ Strategy Generated Successfully!")
                print("=" * 60)
                print(f"\n📁 Saved to: {output_file}")
                print(f"\n📊 Preview (first 500 chars):")
                print("-" * 60)
                print(analysis[:500] + "...")
                print("-" * 60)
                exit(0)
    
    print(f"❌ Unexpected response format: {result}")
    exit(1)
    
except requests.exceptions.Timeout:
    print("❌ Request timeout (90s)")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    if 'response' in locals():
        print(f"Response: {response.text[:300]}")
    exit(1)
