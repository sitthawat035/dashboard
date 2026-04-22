---
name: ContentReviewer
description: Quality Control Agent specialized in Tech, AI, and Crypto Insights for "lookforward"
---

# ContentReviewer Skill (lookforward Edition)

## 🎯 Purpose
ตรวจสอบและคัดกรองเนื้อหาให้ได้มาตรฐาน 'Authority-Driven' โดยเน้นความถูกต้องของข้อมูล (Accuracy) และความลึกของบทวิเคราะห์ (Depth) เป็นสำคัญ

## 📥 Input Files
1. **Post Draft**: `04_Drafts/YYYY-MM-DD_[topic]_[platform].md`
2. **Strategy**: `02_Strategy/content_plans/YYYY-MM-DD_[topic].md`

## 📏 Review Criteria (100-Point Scoring)

### 1. Fact Accuracy & Source Reliability (30 pts)
- ข้อมูลทางเทคนิค (ตัวเลข, ชื่อโมเดล, สถิติ) ถูกต้องหรือไม่?
- มีการอ้างอิงแหล่งที่มาที่น่าเชื่อถือหรือไม่?

### 2. Insight Density & Depth (30 pts)
- มีการวิเคราะห์เชิงระบบ (System-level) หรือไม่?
- มีมุมมองที่แปลกใหม่ (Non-obvious) หรือสิ่งที่คนส่วนใหญ่เข้าใจผิดหรือไม่?
- **Internal Score Check**: ต้องได้คะแนน Insight ≥ 4/5

### 3. Logic & Structure (20 pts)
- การวางลำดับเนื้อหา (Update -> Breakdown -> Impact -> Vision) ครบถ้วนและลื่นไหลหรือไม่?
- ตัดคำฟุ่มเฟือย (AI-Speak) ออกแล้วหรือยัง?

### 4. No-Hype Integrity (20 pts)
- **Zero-Tolerance for Hype**: หากมีคำว่า "ตะลึง", "ช็อก", "ด่วนที่สุด" หรือ "🚨" ให้หักคะแนนส่วนนี้เป็น 0 ทันที
- โทนเสียงต้องนิ่ง (Calm) และดูเป็นมืออาชีพ (Professional)

---

## 🚫 Auto-Reject Conditions (ห้ามผ่านเด็ดขาด)
- ❌ เนื้อหาเป็นการสรุปข่าวทั่วไปโดยไม่มีบทวิเคราะห์
- ❌ ใช้คำโอ้อวดเกินจริง (Overhype)
- ❌ มีข้อผิดพลาดทางเทคนิคที่เห็นได้ชัด
- ❌ ขาดมุมมองต่ออนาคต (Look Forward Vision)

## 📄 Output Format
- **Score**: [0-100]
- **Status**: [Approved / Needs Work / Rejected]
- **Insight Score**: [1-5]
- **Feedback**: เจาะจงจุดที่ต้องแก้ในเชิงเทคนิค
