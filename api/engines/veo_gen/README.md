# 🎬 VEO Video Prompt Engine (v1.0)
🚀 **Engine Hub Integration - OpenClaw Dashboard**

Engine นี้ถูกออกแบบมาเพื่อวิเคราะห์รูปภาพสินค้าและสร้าง Prompt สำหรับการเจนวิดีโอคุณภาพสูงใน **Google Flow Labs (Veo 3.1 / Nano Banana 2)** โดยเน้นที่ความถูกต้องของสินค้า 100% (Product Integrity) และความต่อเนื่องของตัวละคร (Character DNA)

---

## 📂 โครงสร้างไฟล์ (Files)
- manual_veo.py: สคริปต์หลัก (Engine) รองรับทั้ง CLI และ Dashboard API
- config.json: ไฟล์ตั้งค่า (สัดส่วน, ความยาว, สไตล์, AI Model)
- SystemPrompt_New.txt: หัวใจของ Engine (คำสั่งลับสำหรับล็อคสินค้าและตัวละคร)
- .env: เก็บ OPENROUTER_API_KEY (สำคัญมาก ห้ามลบ)
- input_product.jpg: รูปสินค้าเริ่มต้นที่ Engine จะดึงไปวิเคราะห์

---

## ⚙️ การตั้งค่า (Configuration)
คุณสามารถปรับแต่ง Option ต่างๆ ได้ที่ config.json:
- model_name: รุ่นของ AI (ค่าเริ่มต้น: google/gemini-2.0-flash-001)
- spect_ratio: สัดส่วน (9:16, 16:9, 1:1)
- duration: ความยาววิดีโอ (5s, 8s, 10s)
- style: สไตล์โฆษณา (Commercial, Cinematic, Minimal)

---

## 🚀 วิธีใช้งาน (Usage)

### 1. ผ่าน Dashboard (แนะนำ)
- เข้าไปที่หน้า **Engine Hub** บน Dashboard
- เลือก **"VEO Video Prompt Gen"**
- กดปุ่ม **OPTIONS** เพื่อเลือกสัดส่วนและความยาวที่ต้องการ
- กด **RUN ENGINE** และรอรับ Prompt ที่หน้าจอ **LIVE OUTPUT**

### 2. ผ่าน Terminal (CLI)
`ash
python manual_veo.py --image "ทางไปรูป.jpg"
`
หรือรันแบบปกติเพื่อใช้รูปดีฟอลต์:
`ash
python manual_veo.py
`

---

## 🎬 Workflow การเจนวิดีโอ (Step-by-Step)

### STEP 1: สร้างรูป Keyframe
1. เข้าเว็บ: [Google Flow Labs](https://labs.google/fx/th/tools/flow)
2. อัปโหลดรูปสินค้าต้นฉบับ
3. คัดลอก **Prompt Step 1** จาก Engine ไปวางในแชท
4. เลือกโมเดล **"Nano Banana 2"** และกด Enter

### STEP 2: สร้างวิดีโอ (Veo 3.1)
1. เมื่อรูปใน Step 1 เสร็จแล้ว ให้กดปุ่ม **"เริ่ม" (Start)** ที่รูปนั้น
2. คัดลอก **Prompt Step 2** จาก Engine ไปวางในช่องแชทใหม่
3. เลือกโมเดล **"Veo 3.1"** และกด Enter
4. รอรับวิดีโอ 8-10 วินาที พร้อมเสียงพากย์และสินค้าที่เหมือนเดิม 100%!

---

## 🧬 Key Features
- **Product Consistency:** บังคับ AI ให้รักษาโลโก้ สี และรูปทรงสินค้าให้เหมือนรูปต้นฉบับ
- **Character DNA:** ล็อคหน้าตาและชุดของโมเดลให้เหมือนกันตลอดทุกคลิป
- **Voice Over Integration:** รวม Script พากย์เสียงไทยเข้ากับ Prompt โดยอัตโนมัติ

---
*Created by Gemini CLI Assistant for JoePV Core Hub*
