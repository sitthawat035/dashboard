---
description: บังคับใช้ระบบ 4-Stage Pipeline (Analysis > Backend > Frontend > Review) เพื่อการเขียนโค้ด Full-Stack ที่แม่นยำและลด Error
---

# THE FULL-STACK WORKFLOW PROTOCOL

ทุกครั้งที่มีคำสั่งสร้าง Feature ใหม่ แก้ไข Code หรือแก้ Bug ให้รันตามลำดับนี้โดยอัตโนมัติ โดยใช้ระบบ **Spawn Subagent** เพื่อแยก Session การทำงานให้เป็นระเบียบ:

### STAGE 1: SYSTEM ANALYST (วิเคราะห์ระบบและวางแผน)
- **Task:** สแกน Codebase ทั้งหมดเพื่อทำความเข้าใจ Requirement และวิเคราะห์ผลกระทบ
- **Output:** สร้าง "Implementation Plan" (Step-by-step Task List โดยแยกส่วน Backend และ Frontend ชัดเจน)
- **Tooling:** ดำเนินการโดย Main Agent หลัก
- **Constraint:** **ห้ามเขียนโค้ดเอง** ให้วางโครงสร้างระบบ แล้วส่งต่อให้ Stage ถัดไป

### STAGE 2: BACKEND DEVELOPER (พัฒนาระบบหลังบ้าน)
- **Task:** ลงมือแก้ไข/เขียนโค้ดฝั่ง Backend (API, Data Models, Logic)
- **Delegation:** ใช้คำสั่ง `sessions_spawn({ agentId: "backend-dev", message: "ทำตามแผนส่วน Backend: [รายละเอียด]" })` 
- **Quality:** โค้ดคลีน, จัดการ Error Handling ฝั่งเซิร์ฟเวอร์
- **Constraint:** โฟกัสเฉพาะ Backend เมื่อเสร็จแล้วส่งผลลัพธ์กลับมาเพื่อไป Stage ถัดไป

### STAGE 3: FRONTEND DEVELOPER (พัฒนาระบบหน้าบ้าน)
- **Task:** สร้างหรือแก้ไขคอมโพเนนต์ฝั่งหน้าบ้าน (UI, State) และ Integrate API
- **Delegation:** ใช้คำสั่ง `sessions_spawn({ agentId: "frontend-dev", message: "ทำตามแผนส่วน Frontend: [รายละเอียด]" })`
- **Quality:** UI ครบถ้วน, จัดการสถานะ Loading/Error/Success
- **Constraint:** ยึดตามจุดเชื่อมต่อของ Backend อย่างเคร่งครัด

### STAGE 4: REVIEWER & QA (ผู้ตรวจสอบมาตรฐาน E2E)
- **Task:** ทดสอบการทำงานรวมทั้งระบบ (End-to-End)
- **Delegation:** ใช้คำสั่ง `sessions_spawn({ agentId: "qa-verifier", message: "ตรวจสอบงานทั้งหมด: [Link/Task]" })`
- **Success Criteria:** 
  1. Frontend สื่อสารกับ Backend ได้สมบูรณ์ ไม่มี Error บน Console
  2. ฟังก์ชันทำงานได้ตรงตามโจทย์
- **Verdict:**
  - **FAIL:** ส่งกลับไปยัง Stage ที่เกี่ยวข้องทันที
  - **PASS:** แจ้งสรุปว่า "ผ่านการตรวจสอบทั้งหมดประเมินว่างานเสร็จสมบูรณ์"

# MULTI-AGENT ORCHESTRATION TOOLS
- **Sequential Spawn:** `sessions_spawn({ agentId: "ID", message: "MSG" })` - ใช้เมื่อต้องการส่งงานต่อเป็นทอดๆ
- **Parallel Spawn:** `subagents([{ agentId: "ID1", message: "MSG1" }, { agentId: "ID2", message: "MSG2" }])` - ใช้เมื่อต้องการให้ Backend และ Frontend เริ่มงานพร้อมกัน (ถ้าแผนชัดเจนแล้ว)
- **CLI Fallback:** หาก Tool ใน Session ไม่ทำงาน ให้ใช้ `openclaw agent --agent [ID] --message "[MSG]" --json` ผ่าน Terminal

# ERROR HANDLING
- หากเกิดปัญหากระดุม "Request Approval" ไม่ขึ้น ให้พิมพ์คำสั่งในรูปแบบ Markdown ```bash เสมอ
- **ห้าม** ใช้ `2>&1` ในคำสั่งรันปกติเว้นแต่จำเป็น และห้ามรันซ้ำหาก User แจ้งว่าค้าง
