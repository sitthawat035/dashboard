# ContentReviewer Usage Guide

**Purpose**: ตรวจสอบและคัดกรองเนื้อหาให้ได้มาตรฐาน 'Authority-Driven' โดยเน้นความถูกต้องของข้อมูล (Accuracy) และความลึกของบทวิเคราะห์ (Depth) เป็นสำคัญ สำหรับเพจ **"lookforward"**

---

## 🎯 Core Mission

ตรวจสอบเนื้อหาให้:
- **Fact-Accurate** (ข้อมูลถูกต้อง ตรวจสอบได้)
- **Insight-Dense** (มีมุมมองเชิงลึกที่ไม่ธรรมดา)
- **Hype-Free** (ไม่มีคำโอ้อวดเกินจริง)
- **Authority-Ready** (พร้อมสร้างความน่าเชื่อถือ)

---

## 📏 Review Criteria (100-Point Scoring)

### 1. Fact Accuracy & Source Reliability (30 pts)
- ข้อมูลทางเทคนิค (ตัวเลข, ชื่อโมเดล, สถิติ) ถูกต้องหรือไม่?
- มีการอ้างอิงแหล่งที่มาที่น่าเชื่อถือหรือไม่?

**Scoring:**
- 30 pts: ข้อมูลถูกต้อง 100%, มีแหล่งอ้างอิง
- 20 pts: ข้อมูลถูกต้องส่วนใหญ่
- 10 pts: มีข้อผิดพลาดเล็กน้อย
- 0 pts: ข้อมูลผิดพลาดหรือไม่มีแหล่งอ้างอิง

### 2. Insight Density & Depth (30 pts)
- มีการวิเคราะห์เชิงระบบ (System-level) หรือไม่?
- มีมุมมองที่แปลกใหม่ (Non-obvious) หรือสิ่งที่คนส่วนใหญ่เข้าใจผิดหรือไม่?
- **Internal Score Check**: ต้องได้คะแนน Insight ≥ 4/5

**Scoring:**
- 30 pts: Insight Score 5/5 (Excellent - มุมมองที่ไม่เคยมีใครพูดถึง)
- 25 pts: Insight Score 4/5 (Good - มี Insight เฉียบคมและเชื่อมโยงระบบได้)
- 15 pts: Insight Score 3/5 (Fair - เริ่มมีการวิเคราะห์รายข้อ)
- 5 pts: Insight Score 2/5 (Weak - อธิบายข้อมูลเบื้องต้น)
- 0 pts: Insight Score 1/5 (Reject - สรุปข่าวทั่วไป)

### 3. Logic & Structure (20 pts)
- การวางลำดับเนื้อหา (Update → Breakdown → Impact → Vision) ครบถ้วนและลื่นไหลหรือไม่?
- ตัดคำฟุ่มเฟือย (AI-Speak) ออกแล้วหรือยัง?

**Scoring:**
- 20 pts: โครงสร้างสมบูรณ์ ลื่นไหล อ่านง่าย
- 15 pts: โครงสร้างดี มีจุดปรับปรุงเล็กน้อย
- 10 pts: โครงสร้างพอใช้ ต้องปรับปรุง
- 0 pts: โครงสร้างไม่ชัดเจน สับสน

### 4. No-Hype Integrity (20 pts)
- **Zero-Tolerance for Hype**: หากมีคำว่า "ตะลึง", "ช็อก", "ด่วนที่สุด" หรือ "🚨" ให้หักคะแนนส่วนนี้เป็น 0 ทันที
- โทนเสียงต้องนิ่ง (Calm) และดูเป็นมืออาชีพ (Professional)

**Scoring:**
- 20 pts: ไม่มีคำ hype เลย, โทนมืออาชีพ
- 10 pts: มีคำที่เกินจริงเล็กน้อย
- 0 pts: มีคำ hype หรือ clickbait

---

## 🚀 Quick Start

### 1. Review Content Draft
```powershell
# Review single draft
python .agent/skills/ContentReviewer/reviewer.py --draft 04_Drafts/2026-02-08/deepseek_architecture_facebook.md

# Review all drafts from today
python .agent/skills/ContentReviewer/reviewer.py --date 2026-02-08

# Review with auto-approve threshold
python .agent/skills/ContentReviewer/reviewer.py --draft path/to/draft.md --auto-approve 85
```

---

## 📄 Output Format

Creates review report in `04_Drafts/YYYY-MM-DD/`:

```markdown
# Content Review Report

**Draft**: deepseek_architecture_facebook.md  
**Reviewed**: 2026-02-08 03:30:00  
**Reviewer**: ContentReviewer v2.0

---

## 📊 Overall Score: 92/100

**Status**: ✅ **APPROVED**  
**Insight Score**: 4/5  
**Grade**: A (Excellent)

---

## Detailed Scoring

### 1. Fact Accuracy & Source Reliability: 28/30
✅ Technical data verified (DeepSeek training cost, benchmarks)  
✅ Source cited (ArXiv research paper)  
⚠️ Minor: Could add specific benchmark names

### 2. Insight Density & Depth: 28/30
✅ Non-obvious angle: "architecture > budget"  
✅ Systemic connection: democratization of AI  
✅ Future vision: shift from monopoly to open innovation  
⚠️ Could explore deeper: impact on AI startups

### 3. Logic & Structure: 18/20
✅ Clear flow: Update → Breakdown → Impact → Vision  
✅ No AI-speak detected  
⚠️ Minor: CTA could be stronger

### 4. No-Hype Integrity: 18/20
✅ No hype words detected  
✅ Professional tone maintained  
⚠️ Minor: Emoji usage is minimal but acceptable

---

## 💡 Feedback & Recommendations

### Strengths
- Excellent systemic analysis
- Clear technical breakdown
- Strong non-obvious angle
- Professional tone throughout

### Improvements
1. Add specific benchmark names (e.g., "MMLU", "HumanEval")
2. Strengthen CTA with more specific value proposition
3. Consider adding one more data point for impact section

### Suggested Edits
```diff
- Competitive กับ GPT-4 บน standard benchmarks
+ Competitive กับ GPT-4 บน MMLU (89.5%) และ HumanEval benchmarks
```

---

## 🎯 Recommendation

**Action**: APPROVED for publishing  
**Next Step**: Move to `04_Drafts/approved/`  
**Optional**: Apply suggested edits for even higher quality

---

**Review Confidence**: High  
**Estimated Engagement Potential**: 6-8% (above average)
```

---

## 🚫 Auto-Reject Conditions

Content will be **automatically rejected** if:

❌ **เนื้อหาเป็นการสรุปข่าวทั่วไปโดยไม่มีบทวิเคราะห์** (Insight Score < 3)  
❌ **ใช้คำโอ้อวดเกินจริง** (Overhype) - "ตะลึง", "ช็อก", "🚨"  
❌ **มีข้อผิดพลาดทางเทคนิคที่เห็นได้ชัด** (Fact Accuracy < 15/30)  
❌ **ขาดมุมมองต่ออนาคต** (Look Forward Vision)

---

## 📊 Scoring Thresholds

| Score Range | Grade | Status | Action |
|-------------|-------|--------|--------|
| 90-100 | A (Excellent) | ✅ Approved | Publish immediately |
| 85-89 | B+ (Very Good) | ✅ Approved | Minor edits optional |
| 75-84 | B (Good) | ⚠️ Needs Work | Apply suggested edits |
| 60-74 | C (Fair) | ⚠️ Needs Work | Major revision required |
| < 60 | F (Fail) | ❌ Rejected | Rewrite from scratch |

---

## 📥 Input Files

1. **Post Draft**: `04_Drafts/YYYY-MM-DD_[topic]_[platform].md`
2. **Strategy** (optional): `02_Strategy/content_plans/YYYY-MM-DD_[topic].md`

---

## 🔗 Next Steps After Review

### If Approved (Score ≥ 85)
```powershell
# Move to approved folder
Move-Item 04_Drafts/2026-02-08/draft.md 04_Drafts/approved/

# Schedule for publishing
python .agent/skills/ContentScheduler/scheduler.py --draft 04_Drafts/approved/draft.md
```

### If Needs Work (Score 75-84)
```powershell
# Apply suggested edits
# Re-run review
python .agent/skills/ContentReviewer/reviewer.py --draft path/to/edited_draft.md
```

### If Rejected (Score < 75)
```powershell
# Move to rejected folder
Move-Item 04_Drafts/2026-02-08/draft.md 04_Drafts/rejected/

# Generate new draft with feedback
python .agent/skills/ContentWriter/writer.py --strategy path/to/strategy.md --feedback path/to/review.md
```

---

## 💡 Pro Tips

1. **Trust the scoring** - It's calibrated for authority content
2. **Don't skip Insight Score** - This is the most critical metric
3. **Zero tolerance for hype** - Protect brand integrity
4. **Fact-check everything** - One error destroys credibility
5. **Iterate on 75-84 scores** - They're worth improving

---

**Version**: 2.0 (Authority Edition)  
**Last Updated**: 2026-02-08  
**Alignment**: lookforward Brand (Tech Authority)
