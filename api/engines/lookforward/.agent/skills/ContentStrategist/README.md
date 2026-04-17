# ContentStrategist Usage Guide

**Purpose**: วิเคราะห์แนวโน้มเทคโนโลยี (AI, Tech, Crypto) เพื่อวางกลยุทธ์เนื้อหาที่เน้นการสร้าง Authority และ Trust โดยเน้นการหา 'Insight' ที่คนส่วนใหญ่พยายามมองข้าม สำหรับเพจ **"lookforward"**

---

## 🎯 Core Mission

สร้างกลยุทธ์เนื้อหาที่:
- **มีความลึก** (Systemic Analysis) ไม่ใช่แค่สรุปข่าว
- **มี Insight** (Non-obvious Angle) ที่คนทั่วไปมองข้าม
- **มีคุณค่า** (Authority Building) สร้างความน่าเชื่อถือระยะยาว

---

## 🧠 Strategy Process: The Authority Blueprint

### Step 1: Trend Deconstruction (ชำแหละเทรนด์)
- วิเคราะห์ว่าข่าวหรือเทคโนโลยีที่เกิดขึ้น มีกลไก (Mechanism) การทำงานอย่างไร
- แยกแยะระหว่าง "Hype" (กระแสปั่น) กับ "Real Value" (คุณค่าจริง)

### Step 2: Systemic Connection (เชื่อมโยงระบบ)
- มองหาความเชื่อมโยง: เทคโนโลยีนี้ส่งผลกระทบต่อระบบอื่นอย่างไร?
- เช่น "ชิปตัวใหม่ของ NVIDIA ไม่ได้แค่แรงขึ้น แต่จะเปลี่ยนโครงสร้างต้นทุนการทำ Model Training ของบริษัท Tech ทั่วโลก"

### Step 3: Insight Extraction (กลั่นกรองมุมมองใหม่)
- **Mandatory**: ต้องหามุมมองที่ "ไม่ปกติ" (Non-obvious Angle)
- ตั้งคำถาม: "คนส่วนใหญ่เข้าใจเรื่องนี้ผิดตรงไหน?" หรือ "อะไรคือสาเหตุที่แท้จริง (Root Cause) ที่ไม่มีใครพูดถึง?"
- **Insight Score Goal**: วางแผนเนื้อหาเพื่อให้ได้คะแนน 4/5 ขึ้นไปเท่านั้น

### Step 4: Vision Casting (มองไปข้างหน้า)
- คาดการณ์สิ่งที่อาจจะเกิดขึ้นในก้าวถัดไป (What's Next?)
- วางโครงสร้าง Takeaway ที่คนอ่านสามารถนำไปใช้ปรับวิธีคิดหรือการทำงานได้ทันที

---

## 🚀 Quick Start

### 1. Run Strategy Analysis
```powershell
# Analyze tech trend from research
python .agent/skills/ContentStrategist/strategist.py --trends 01_Research/trends/2026-02-08/tech_trends.json

# Analyze specific trend
python .agent/skills/ContentStrategist/strategist.py --trend "DeepSeek R1 Architecture"

# Custom output directory
python .agent/skills/ContentStrategist/strategist.py --trends path/to/trends.json --output 02_Strategy/content_plans
```

---

## 📄 Output Format: Content Plan

Creates markdown files in `02_Strategy/content_plans/YYYY-MM-DD/`:

```markdown
# Content Strategy: [Topic Name]

## 📊 Trend Analysis
- **Topic**: DeepSeek R1 Architecture
- **Source**: ArXiv Research Paper
- **Technical Significance**: High
- **Hype vs Real Value**: Real Value (proven benchmarks)

## 🧠 Core Angle (Systemic Perspective)
"DeepSeek ไม่ได้แค่ถูกกว่า แต่มันเปลี่ยนโครงสร้างต้นทุน AI ของโลก"

## 🔍 Key Technical Points
1. Training cost: $5.6M (vs GPT-4: $100M+)
2. Open-source architecture
3. Competitive with GPT-4 on benchmarks
4. MoE (Mixture of Experts) efficiency

## 🔮 Future Vision (What's Next?)
- Democratization of AI development
- Shift from "who has most money" to "who has best architecture"
- Potential impact on AI startup landscape

## ✍️ Drafting Instructions (for ContentWriter)
- **Tone**: Calm & Sharp (No Hype)
- **Structure**: Update → Breakdown → Impact → Vision
- **Emphasis**: Focus on systemic change, not just cost savings
- **Avoid**: "ตะลึง", "ช็อก", "🚨" - maintain professional authority
- **Target Insight Score**: 4-5/5

## 📸 Media Requirements
- Technical diagrams (architecture comparison)
- Cost comparison charts
- Benchmark performance graphs
```

---

## 🚨 Guardrails

❌ **ห้ามเลือกเทรนด์ที่เป็นเพียงข่าวลือที่ไม่มีมูลความจริง**  
❌ **ห้ามเน้นการทำ Content เพื่อเรียกยอด Engagement เพียงอย่างเดียว**  
❌ **หากเทรนด์นั้นไม่มี Insight ที่ลึกพอ ให้เลือกที่จะไม่ทำ** (Quality over Quantity)

---

## 📥 Input Files

1. **Trend Data**: `01_Research/trends/YYYY-MM-DD/tech_trends.json`
   - Contains: trend name, source, technical facts, significance

---

## 🔗 Next Steps After Strategy

Use the output with:
```powershell
# Generate authority content
python .agent/skills/ContentWriter/writer.py --strategy 02_Strategy/content_plans/2026-02-08/deepseek_architecture.md

# Or run full pipeline
python run_pipeline.py --skip-trends --topic "DeepSeek Architecture"
```

---

## ✅ Success Criteria

- ✅ Strategy identifies **non-obvious angle** (not just summarizing news)
- ✅ **Systemic connection** is clear (how it impacts broader ecosystem)
- ✅ **Insight Score** target is 4-5/5
- ✅ **Future vision** is specific and actionable
- ✅ **No hype language** in drafting instructions

---

**Version**: 2.0 (Authority Edition)  
**Last Updated**: 2026-02-08  
**Alignment**: lookforward Brand (Tech Authority)
