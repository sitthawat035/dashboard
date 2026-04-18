# 🛡️ Git Survival Guide for Working with AI Agents

คู่มือนี้จัดทำขึ้นเพื่อป้องกันเหตุการณ์ "โค้ดย้อนเวลากลับสู่อดีต" ซึ่งมักเกิดขึ้นเมื่อ AI Agent พยายามจัดระเบียบโค้ดโดยอ้างอิงจากประวัติ Git เก่าๆ โดยที่ผู้ใช้ยังไม่ได้บันทึก (Commit) งานปัจจุบัน

---

## 🚀 1. กฎทอง: "Commit ก่อนเรียก Agent"
ทุกครั้งที่โค้ดอยู่ในสถานะที่รันได้ปกติ และคุณกำลังจะเรียก Agent มาแก้ไขงานชุดใหญ่ **ให้ Commit ไว้ก่อนเสมอ**

### คำสั่งด่วน (รันใน Terminal):
```bash
git add .
git commit -m "SAVE: ก่อนให้ Agent ทำงาน [วันที่]"
```
> [!IMPORTANT]
> การ Commit คือการสร้าง **Checkpoint** ถ้า Agent ทำพัง คุณสามารถกู้คืนกลับมาจุดนี้ได้ทันที

---

## 🛠️ 2. คำสั่งกู้ชีพ (Emergency Commands)

### กรณีที่ 1: Agent ทำพัง แต่อยากย้อนกลับไปจุดที่เพิ่ง Commit ไว้
```bash
git reset --hard HEAD
```

### กรณีที่ 2: Agent สั่ง Reset ผิดตัวจนงานหาย (กู้คืนจาก 'Reflog')
แม้ว่า Agent จะสั่งลบประวัติไปแล้ว Git ยังจำ "ก้าวเดิน" ของเราได้:
1. พิมพ์ `git reflog` เพื่อดูประวัติการขยับทั้งหมด
2. หาบรรทัดที่เป็นสถานะล่าสุดของคุณ (เช่น `HEAD@{1}`)
3. สั่งย้อนกลับ:
```bash
git reset --hard HEAD@{1}
```

---

## 💡 3. คำแนะนำในการสั่งงาน Agent (Prompts)
เพื่อความปลอดภัย คุณสามารถเพิ่มประโยคนี้ในคำสั่ง (Instruction) ได้:
- *"Do NOT use any git commands (reset, checkout, merge) without my explicit permission."*
- *"Work only on the current file system state."*

---

## 📊 4. สรุปความหมายของแต่ละคำสั่ง
- **`git status`**: เช็คว่ามีอะไรที่ยังไม่ได้เซฟบ้าง (ตัวสีแดง = ยังไม่เซฟ)
- **`git add .`**: เลือกทุกอย่างที่แก้ไขเตรียมเซฟ
- **`git commit -m "..."`**: กดปุ่ม "เซฟ" บันทึกลงประวัติ
- **`git log --oneline`**: ดูประวัติการเซฟที่ผ่านมา

---
**สร้างโดย:** Antigravity AI
**วันที่:** 2026-04-18
**สถานะโปรเจค:** Dashboard v4 (Clean Slate) - RESTORED
