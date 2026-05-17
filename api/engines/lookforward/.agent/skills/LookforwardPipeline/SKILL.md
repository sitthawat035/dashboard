---
name: LookforwardPipeline
description: สร้าง Tech Authority Content เป็นภาษาไทย สำหรับเพจ lookforward ด้วย Gemini AI
---

# Skill: Lookforward Pipeline (Tech Authority Content)

## 🎯 Purpose
รัน end-to-end content pipeline สำหรับเพจ **lookforward** (Tech Authority) ตั้งแต่ Research → Strategy → Content → Media Prompts → Ready-to-Post

## 📋 How to Use

### Trigger Commands
- `/lookforward <topic>` - สร้างคอนเทนต์จากหัวข้อที่กำหนด
- "น้องกุ้งขอข่าว <topic> หน่อย" - ภาษาธรรมชาติ

### Required Input
- `<topic>`: หัวข้อเทคโนโลยีที่ต้องการ (เช่น "DeepSeek R1", "GPT-5", "Crypto Regulation")

## 🔄 Pipeline Steps

### Step 1: Strategy Phase
- AI วิเคราะห์เทรนด์และวาง Content Strategy
- เน้น "คุณค่าที่แท้จริง" vs "กระแส"
- Output: `01_strategy.md`

### Step 2: Content Generation
- เขียนเนื้อหาเป็นภาษาไทย
- Tone: Professional, Sharp, Visionary
- เน้น Insight Score 4-5/5
- Output: `02_content.md`, `02_content.json`

### Step 3: Visual Prompts
- สร้าง AI image prompts สำหรับรูปประกอบ
- Output: `03_visual_prompts.md`

### Step 4: Ready-to-Post
- เตรียมไฟล์ในโฟลเดอร์ `09_ReadyToPost`
- Files: `post.txt`, `caption.txt`, `hashtags.txt`

## ⚙️ Execution

### Command
```powershell
python "c:\Users\User\.openclaw\workspace\lookforward\scripts\run_pipeline_gemini.py" "<topic>" --gen-images
```

### Alternative (via BAT)
```powershell
c:\Users\User\.openclaw\workspace\lookforward\scripts\run_lookforward.bat "<topic>"
```

## 📁 Output Location
- Drafts: `workspace/lookforward/data/04_Drafts/[date]/[topic]_[timestamp]/`
- Ready to Post: `workspace/lookforward/data/09_ReadyToPost/[date]/[topic]_[timestamp]/`

## 🎨 Tone Guidelines
- **Professional**: ใช้ภาษาที่เป็นมืออาชีพ
- **Sharp**: มุ่งเน้นมุมมองที่คนส่วนใหญ่มองข้าม
- **Visionary**: มีวิสัยทัศน์อนาคต
- **No Hype**: ไม่ใช้คำว่า "ตื่นตระหนก", "ระเบิด", "ช็อค"

## 📊 Quality Standards
- Insight Score ต้องได้ 4/5 ขึ้นไป ถึงจะ publish
- Factual Foundation → Technical Breakdown → Non-Obvious Angle → Impact Analysis → Future Vision

## 🔔 User Feedback Template
After execution:
1. อ่านผลลัพธ์จาก `data/09_ReadyToPost/[latest]/`
2. สรุปให้ user ว่าเสร็จแล้วพร้อมโพสต์
3. แจ้ง folder location ให้ user ทราบ
