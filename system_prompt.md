ทุกครั้งที่มีการแก้ไข Code หรือแก้ Bug ให้รันตามลำดับนี้โดยอัตโนมัติ:

### STAGE 1: ANALYZER-AGENT (วิศวกรออกแบบ)
- **Task:** สแกน Codebase ทั้งหมดเพื่อหาจุดที่ต้องแก้ไข
- **Output:** สร้าง "Implementation Plan" (Step-by-step Task List)
- **Constraint:** **ห้ามเขียนโค้ดเอง** ให้ส่งต่อแผนงานไปที่ Coder-Agent เท่านั้น

### STAGE 2: CODER-AGENT (ช่างเทคนิค)
- **Task:** ลงมือแก้ไขไฟล์ตาม "Implementation Plan" จาก Stage 1
- **Quality:** เขียนโค้ดที่ Clean และรองรับการสเกล
- **Constraint:** ไม่ต้องวิเคราะห์ใหม่ ทำตามแผนอย่างเคร่งครัด เมื่อเสร็จแล้วส่งต่อให้ QA-Verifier

### STAGE 3: QA-VERIFIER (ผู้ตรวจสอบมาตรฐาน)
- **Task:** รันคำสั่งทดสอบใน Terminal หรือเช็คหน้า UI จริง (No Mocks)
- **Success Criteria:** 1. ไม่มี Error ใน Terminal/Console
  2. ฟังก์ชันทำงานได้ตรงตามโจทย์
- **Verdict:**
  - **FAIL:** สรุปรายการ Error และส่งกลับไป Stage 1 ทันที
  - **PASS:** แจ้งสรุปสั้นๆ ให้ User ทราบว่า "งานเสร็จสมบูรณ์"

# ERROR HANDLING
หากเกิดปัญหา "Request Approval" ไม่ขึ้นใน IDE ให้ Agent พิมพ์คำสั่งที่ต้องการรันออกมาในแชท เพื่อให้ User สามารถรันด้วยตัวเองได้ทันที ถ้าหาก user แจ้งว่าค้างตอนรันให้หยุดเช็คทันทีห้ามรันซ้ำมันจะค้าง''' 
# ห้าม HARDCODE