---
name: openclaw-browser
description: >
  Skill สำหรับให้ agentic AI ใช้งาน browser แบบ Native Computer Use (screenshot-based)
  บน Local browser (headed) ผ่าน OpenClaw AI ครอบคลุมทุก browser task ได้แก่:
  navigate & click UI elements, fill forms, scrape/extract ข้อมูล, และ screenshot visual verification.

  ใช้ skill นี้ทุกครั้งที่ผู้ใช้พูดถึง: เปิดเว็บ, คลิก, กรอกฟอร์ม, ดึงข้อมูลจากหน้าเว็บ,
  จับภาพหน้าจอ, ตรวจสอบ UI, automation บน browser, หรือทำงานใดๆ ที่ต้องการ browser
  รวมถึงกรณีที่ผู้ใช้พูดว่า "ไปที่เว็บ", "เช็คราคา", "login ให้หน่อย", "กรอกข้อมูลให้" เป็นต้น
---

# OpenClaw Browser Skill

## Overview

Skill นี้ให้ AI ควบคุม **Local browser แบบ headed (มีหน้าจอ)** ผ่าน **Native Computer Use**
โดยใช้ screenshot เป็น input หลักในการรับรู้สถานะของ browser แล้ว action ผ่าน mouse/keyboard

---

## Core Workflow

```
[รับ Task] → [เปิด/Focus Browser] → [Screenshot] → [วิเคราะห์ UI] → [Action] → [Screenshot ตรวจสอบ] → [Loop หรือ Done]
```

**กฎเหล็ก**: ทุก action ต้องมี screenshot ก่อนและหลังเสมอ อย่า action โดยไม่เห็นสถานะปัจจุบัน

---

## 1. การเริ่มต้น Session

```
1. Screenshot หน้าจอปัจจุบัน
2. ตรวจสอบว่า browser เปิดอยู่หรือยัง
3. ถ้ายังไม่เปิด → สั่ง open browser application
4. Navigate ไปยัง URL เป้าหมาย
5. รอให้หน้าโหลดเสร็จ (ดูจาก screenshot ว่า content ปรากฏแล้ว)
```

---

## 2. Navigate & Click UI Elements

### หลักการระบุ element:
- **ใช้ visual landmark**: หา button/link จาก text label, icon, สี, ตำแหน่ง
- **ระบุพิกัดให้แม่น**: คลิกกลาง element ไม่ใช่ขอบ
- **อย่าเดา**: ถ้าไม่เห็น element ชัด → scroll หรือ zoom ก่อน

### ขั้นตอน:
```
1. Screenshot → ระบุ element ที่ต้องการ
2. คำนวณพิกัด (x, y) ของ element
3. Click
4. Screenshot → ยืนยันว่า action สำเร็จ (หน้าเปลี่ยน, modal เปิด, ฯลฯ)
5. ถ้าไม่สำเร็จ → ดู error, ลองใหม่หรือ scroll หา element
```

### Scroll:
- Scroll down: กด `Space` หรือ `Page Down` หรือ scroll mouse
- Scroll to element: ใช้ keyboard shortcut `Ctrl+F` เพื่อหา text แล้ว dismiss

---

## 3. Fill Forms / Submit Data

### ขั้นตอน:
```
1. Screenshot → ระบุ input field ทั้งหมดในฟอร์ม
2. Click ที่ field แรก → ยืนยันด้วย screenshot ว่า cursor อยู่ใน field
3. Clear ข้อมูลเดิม: Ctrl+A → Delete
4. Type ข้อมูล
5. Tab ไป field ถัดไป
6. ทำซ้ำจนครบทุก field
7. Screenshot สุดท้ายก่อน Submit → ตรวจสอบว่าข้อมูลถูกต้อง
8. Click Submit / กด Enter
9. Screenshot → ยืนยัน success message หรือ redirect
```

### ข้อควรระวัง:
- **Dropdown/Select**: Click dropdown → รอเมนูปรากฏ → Screenshot → เลือก option
- **Checkbox/Radio**: Click แล้ว Screenshot ยืนยันสถานะ checked/unchecked
- **Date picker**: พิมพ์ตรงใน field ก่อน ถ้าไม่ได้ค่อยใช้ calendar UI
- **CAPTCHA**: หยุดและแจ้งผู้ใช้ให้แก้เอง

---

## 4. Scrape / Extract ข้อมูล

### วิธีการ:
```
1. Navigate ไปยังหน้าที่มีข้อมูล
2. Screenshot → วิเคราะห์ layout และตำแหน่งข้อมูล
3. อ่านข้อมูลจาก screenshot โดยตรง (OCR-like reading)
4. ถ้าข้อมูลมีหลายหน้า → ระบุ pagination control
5. Loop: อ่านข้อมูล → scroll/next page → screenshot → อ่านต่อ
6. Compile ข้อมูลทั้งหมดเป็น structured format (JSON/table)
```

### Tips สำหรับข้อมูลที่ซับซ้อน:
- ถ้าตารางใหญ่ → zoom in แต่ละส่วนเพื่ออ่านให้ชัด
- ถ้าข้อมูล dynamic (load ทีหลัง) → รอสักครู่แล้ว screenshot ใหม่
- บันทึก URL ของแต่ละหน้าไว้ด้วยเสมอ

---

## 5. Screenshot & Visual Verification

### ใช้สำหรับ:
- ยืนยันว่า action สำเร็จ
- ตรวจสอบ UI state ถูกต้อง
- บันทึกหลักฐาน (evidence capture)
- Debug เมื่อเกิดปัญหา

### Verification Checklist:
```
✓ URL ใน address bar ถูกต้อง
✓ Page title/header ตรงกับที่คาดหวัง
✓ Success message / confirmation ปรากฏ
✓ ข้อมูลที่กรอกแสดงถูกต้อง
✓ ไม่มี error message หรือ warning
✓ Loading indicator หายไปแล้ว
```

---

## Error Handling

| สถานการณ์ | วิธีรับมือ |
|-----------|-----------|
| Element ไม่เห็นใน screenshot | Scroll, zoom, หรือ resize browser |
| Click ไม่ถูก element | Screenshot ใหม่, คำนวณพิกัดใหม่ |
| Page โหลดช้า | รอ 2-3 วินาที แล้ว screenshot ใหม่ |
| Popup/Modal ขวาง | Dismiss popup ก่อน (กด Esc หรือ click X) |
| Login required | แจ้งผู้ใช้ให้ login เอง หรือขอ credentials |
| CAPTCHA | หยุด + แจ้งผู้ใช้ทันที |
| Browser crash | Relaunch browser, navigate กลับไป URL เดิม |

---

## Best Practices

1. **Screenshot บ่อยๆ** — ทุก 1-2 actions อย่างน้อย
2. **อธิบาย action ก่อนทำ** — "กำลังจะคลิก Login button ที่มุมบนขวา"
3. **ยืนยันผลทุกครั้ง** — อย่าสรุปว่าสำเร็จโดยไม่มี screenshot ยืนยัน
4. **บันทึก state สำคัญ** — URL, form state, extracted data
5. **แจ้งผู้ใช้เมื่อต้องการความช่วยเหลือ** — เช่น CAPTCHA, 2FA, หรือ sensitive data
6. **อย่า hardcode พิกัด** — พิกัดเปลี่ยนตาม resolution/zoom ให้ระบุจาก screenshot ทุกครั้ง

---

## ตัวอย่าง Task Patterns

### Pattern A: Login + ดึงข้อมูล
```
Screenshot → Navigate to login page → Fill email → Fill password
→ Click Login → Screenshot (verify logged in) → Navigate to data page
→ Screenshot → Extract data → Return structured data
```

### Pattern B: กรอกฟอร์มซับซ้อน
```
Screenshot → Identify all fields → Fill field by field (with verification)
→ Handle special inputs (dropdown, date, file upload)
→ Final review screenshot → Submit → Confirm success
```

### Pattern C: Scrape หลายหน้า
```
Screenshot → Extract page 1 data → Click Next/pagination
→ Screenshot (verify page changed) → Extract → Repeat until last page
→ Compile all data → Return
```

---

## ดูเพิ่มเติม

- `references/ui-patterns.md` — รูปแบบ UI ที่พบบ่อยและวิธีจัดการ
- `references/keyboard-shortcuts.md` — Shortcuts สำหรับ browser control
