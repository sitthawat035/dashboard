# ContentWriter Usage Guide

**Purpose**: เปลี่ยนข้อมูลดิบหรือกลยุทธ์ให้กลายเป็นบทความวิเคราะห์เทคโนโลยีที่ลุ่มลึก น่าเชื่อถือ และสร้างความเชื่อมั่น (Authority) ให้กับเพจ **"lookforward"**

---

## 🎯 Core Mission

เขียนเนื้อหาที่:
- **Fact-Driven** (ข้อมูลถูกต้อง ตรวจสอบได้)
- **Calm & Sharp** (นิ่งแต่เฉียบคม ไม่ overhype)
- **Insight-Dense** (มีมุมมองที่คนทั่วไปมองข้าม)
- **Authority-Building** (สร้างความน่าเชื่อถือระยะยาว)

---

## ✍️ Writing Process: The Synthesis Framework

### Step 1: The Update (Fact-Driven Start)
- เริ่มต้นด้วยข้อมูลเทคโนโลยีหรือข่าวสารที่เกิดขึ้นจริง
- **Rule**: ห้ามใช้ Clickbait หรือคำ Overhype เช่น "ด่วน", "🚨"
- **Goal**: ให้คนอ่านรู้ทันทีว่า "เกิดอะไรขึ้น" แบบมืออาชีพ

### Step 2: Tech Breakdown (Systemic Analysis)
- อธิบายกลไก (Mechanism) หรือรายละเอียดเชิงเทคนิค 3-5 ข้อ
- เน้นความถูกต้องของข้อมูล (Fact Accuracy) และความลึกของเนื้อหา
- **Goal**: ให้คนอ่านเข้าใจ "ระบบ" เบื้องหลังเทคโนโลยีนั้น

### Step 3: The Impact (Real-world Connection)
- วิเคราะห์ว่าสิ่งที่เกิดขึ้นจะส่งผลกระทบต่ออุตสาหกรรม หรือผู้คนอย่างไร
- ใช้เหตุผลนำอารมณ์ (Logic over Emotion)

### Step 4: Look Forward Vision (Future Prediction)
- ให้มุมมองต่ออนาคตว่า "What's Next?"
- **Insight Density**: ต้องมีมุมมองที่คนทั่วไปมองข้าม (Non-obvious)

### Step 5: Value CTA (Authority Building)
- ชวนแลกเปลี่ยนความคิดเห็นเชิงเทคนิค
- ให้เหตุผลที่ชัดเจนในการติดตามเพจ (Follow for Insight)

---

## 🚀 Quick Start

### 1. Generate Authority Content
```powershell
# From strategy file (recommended)
python .agent/skills/ContentWriter/writer.py --strategy 02_Strategy/content_plans/2026-02-08/deepseek_architecture.md

# Direct topic input
python .agent/skills/ContentWriter/writer.py --topic "DeepSeek R1 Architecture" --platform facebook --variations 2

# Multiple platforms
python .agent/skills/ContentWriter/writer.py --strategy path/to/strategy.md --platforms facebook,twitter
```

---

## 📄 Output Format

Creates drafts in `04_Drafts/YYYY-MM-DD/`:

```markdown
# Content Draft: DeepSeek R1 Architecture

**Platform**: Facebook  
**Date**: 2026-02-08  
**Strategy**: 02_Strategy/content_plans/2026-02-08/deepseek_architecture.md

---

## Variation A

DeepSeek R1 ไม่ได้แค่ถูกกว่า แต่มันเปลี่ยนโครงสร้างต้นทุน AI ของโลก

**Technical Breakdown:**
• Training cost: $5.6M (เทียบกับ GPT-4 ที่ $100M+)
• Open-source architecture ที่ทุกคนเข้าถึงได้
• Competitive กับ GPT-4 บน standard benchmarks
• ใช้ MoE (Mixture of Experts) เพิ่มประสิทธิภาพ

**The Impact:**
ปัญหาไม่ได้อยู่ที่ว่า "ใครมีเงินมากกว่า" แต่มันอยู่ที่ "ใครออกแบบ architecture ได้ดีกว่า"

**Look Forward:**
การ democratize AI development จะเปลี่ยนจาก "Big Tech monopoly" สู่ "Open innovation era"

คุณคิดว่าการเปิดกว้าง AI architecture แบบนี้จะส่งผลกระทบต่ออุตสาหกรรมอย่างไร?

ติดตาม lookforward เพื่อไม่พลาดการวิเคราะห์ Tech Insight ในเชิงลึก 🔍

---

**Character Count**: 487  
**Insight Score**: 4/5  
**Hype Check**: ✅ No overhype detected
```

---

## 🎨 Platform Style Guidelines

### Facebook (Primary Authority)
- **Length**: 800-1,500 ตัวอักษร (เน้นความครบถ้วน)
- **Format**: ใช้ Bullet points เพื่อให้อ่านง่ายแต่เนื้อหาแน่น
- **Emojis**: 2-3 ตัวเพื่อเน้นประเด็นสำคัญเท่านั้น

### Twitter/X (Sharp & Witty)
- **Length**: ไม่เกิน 280 ตัวอักษร
- **Format**: 1 Update + 1 Sharp Insight + 1 Future Question

---

## ✅ Quality Checklist (Self-Evaluation)

Before submitting draft, verify:

- [ ] ข้อมูลถูกต้องและแม่นยำ (Fact Accuracy)
- [ ] มีการวิเคราะห์เชิงระบบ (Systemic Thinking)
- [ ] ไม่มีคำ Overhype หรือ Clickbait
- [ ] ให้ความรู้สึก "นิ่งและเฉียบคม" (Calm & Sharp)
- [ ] Insight Score มั่นใจว่าได้ระดับ 4-5 ดาว

---

## 🚨 Forbidden Words (Auto-Reject)

❌ "ตะลึง", "ช็อก", "ด่วนที่สุด"  
❌ "🚨" (emergency emoji)  
❌ "ในยุคปัจจุบัน", "อย่างไรก็ตาม" (AI-speak)  
❌ Clickbait headlines  

---

## 📥 Input Files

1. **Strategy**: `02_Strategy/content_plans/YYYY-MM-DD_[topic].md`
2. **Media**: `03_Media/YYYY-MM-DD_[topic]_summary.md` (optional)

---

## 🔗 Next Steps After Writing

Use the output with:
```powershell
# Review content quality
python .agent/skills/ContentReviewer/reviewer.py --draft 04_Drafts/2026-02-08/deepseek_architecture_facebook.md

# Or run full pipeline
python run_pipeline.py --skip-trends --topic "DeepSeek Architecture"
```

---

## 💡 Pro Tips

1. **Start with facts** - Build credibility first
2. **Find the non-obvious** - What are people missing?
3. **Connect systems** - Show broader impact
4. **Look forward** - What's next?
5. **Stay calm** - Authority doesn't shout

---

**Version**: 2.0 (Authority Edition)  
**Last Updated**: 2026-02-08  
**Alignment**: lookforward Brand (Tech Authority)
