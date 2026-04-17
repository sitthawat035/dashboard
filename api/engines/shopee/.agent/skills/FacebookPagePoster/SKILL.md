---
name: FacebookPagePoster
description: โพสต์คอนเทนต์ (Caption + รูปภาพ + Comment) ลงบน Facebook Page โดยอัตโนมัติ ย้ายไฟล์ไปเก็บที่ 03_Posted เมื่อเสร็จสิ้น
---

## When to use
เมื่อต้องการโพสต์งานที่เตรียมไว้แล้ว, "Post to Facebook", "อัปโหลดลงเพจ", หรือเมื่อจบกระบวนการเขียน Content แล้วต้องการเผยแพร่

## How to execute
**Input**: โฟลเดอร์ใน `02_ReadyToPost` (หรือระบุ Path โดยตรง) ซึ่งต้องประกอบด้วย:
1.  `caption.txt` หรือไฟล์ .md เนื้อหาโพสต์
2.  ไฟล์รูปภาพ (.jpg, .png)

**Process**:

### 1. Verification (ตรวจสอบความพร้อม)
- เช็คว่ามีไฟล์ caption และรูปภาพครบถ้วนใน folder เป้าหมาย
- อ่านเนื้อหา Caption เตรียมไว้ใน Clipboard หรือ Memory

### 2. Browser Automation (ดำเนินการโพสต์)
ใช้ `browser_subagent` หรือ Script เพื่อทำขั้นตอนต่อไปนี้:
1.  **Open Facebook Page**: เข้า URL ของ Page (User ต้อง Logged-in อยู่แล้ว)
2.  **Create Post**: คลิกที่ "Create Post" หรือ "คุณกำลังคิดอะไรอยู่"
3.  **Upload Media**: อัปโหลดรูปภาพทั้งหมดใน Folder
4.  **Paste Caption**: วางข้อความจาก `caption.txt`
5.  **Post**: กดปุ่ม Post
6.  **Comment (Optional)**: ถ้าใน Caption มี Link Affiliate อาจจะไปแปะใน Comment แรก (ตามกลยุทธ์)

### 3. Archiving (เก็บงาน)
- เมื่อโพสต์สำเร็จ ให้ย้าย Folder นั้นจาก `02_ReadyToPost` ไปที่ `03_Posted/YYYY/MM/`
- สร้าง Folder ปี/เดือน เรียงตามปัจจุบันถ้ายังไม่มี

## Example Command
"ช่วยโพสต์งานเช้านี้จาก folder 02_ReadyToPost/2026-02-05/Morning ให้หน่อย"
