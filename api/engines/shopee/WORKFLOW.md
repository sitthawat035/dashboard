# Shopee Affiliate Automation - Updated Workflow

## 🚀 Quick Start (NEW - Simplified)

### One-Command Automation
```bash
cd shopee_affiliate
python tools/daily_content_generator.py
```

**Output:** 4 posts ready in ~5 minutes! ✅

---

## 📋 What It Does

1. **Loads products** from `data/00_ScrapedData/items.csv` (Scraped using Playwright with Advanced Anti-Bot Bypass: Bezier Curves, `domcontentloaded` intervention, and Captcha Retry loops)
2. **AI selects** best 4 products (< 500 THB)
3. **Coverts Links** to Affiliate Links via Playwright (Requires Chrome Debugging Port 9222)
4. **AI writes** captions (สไตล์เพื่อนสายป้ายยา / รองรับ OpenClaw AI ท้องถิ่น และสลับไปใช้ OpenRouter อัตโนมัติถ้าไม่พร้อม)
5. **Downloads** product images
6. **Saves** everything to `data/05_ReadyToPost/YYYY-MM-DD/`

---

## 📁 Output Structure

```
data/05_ReadyToPost/2026-02-14/
├── 08.00/
│   ├── caption.txt
│   └── product_image.webp
├── 12.00/
│   ├── caption.txt
│   └── product_image.webp
├── 18.00/
│   ├── caption.txt
│   └── product_image.webp
└── 22.00/
    ├── caption.txt
    └── product_image.webp
```

---

## 🎯 For น้องกุ้ง (OpenClaw PM)

### Trigger Command
User says: **"ทำ shopee_affiliate วันนี้"**

### Workflow
1. Check WORLD_STATE.json (shopee_affiliate.status)
2. Update status to "active"
3. Run: `python tools/daily_content_generator.py`
4. Verify output (4 folders created)
5. Report to user
6. Update status to "idle"

---

## 🔧 Manual Steps (Old Workflow - Deprecated)

<details>
<summary>Click to expand old workflow</summary>

### 1️⃣ INPUT: เตรียมสินค้า
1. เปิด 00_ScrapedData  ค้นหาสินค้า skincare < 500 บาท
2. เลือก สินค้า 4 ชิ้น ลงใน `product_input_template.md`

### 2️⃣ PLAN: วางแผนคอนเทนต์
```
/DailyContentPlanner
```
- AI เลือก 4 ชิ้นที่ดีที่สุด
- จัดลง slot 08:00, 12:00, 18:00, 22:00

### 3️⃣ LINKS: แปลง Affiliate Link
1. เปิด Chrome port 9222: `chrome --remote-debugging-port=9222`
2. ไปที่ https://affiliate.shopee.co.th/offer/custom_link
3. วางลิงก์ทั้ง 4 ชิ้น (แบบ newline) ลงใน textarea
4. กดปุ่ม **"เอา ลิงก์"**
5. Copy affiliate links ที่ได้ (format: `https://s.shopee.co.th/XXXX`)
6. อัปเดตลิงก์ใน captions

**หรือใช้ Agent:** บอกว่า "แปลง Affiliate Link" พร้อม links ทั้ง 4

### 4️⃣ CAPTIONS: เขียน Caption
```
/CaptionFullWriter
```
- สร้าง caption สไตล์ "เพื่อนสายป้ายยา"
- บันทึกลง `02_ReadyToPost/YYYY-MM-DD/HH.00/`

### 5️⃣ POST: โพสต์ลง Facebook
```
/FacebookPagePoster
```
- Auto-post caption + รูป (หรือ Schedule ไว้ล่วงหน้า)

### 6️⃣ ARCHIVE: เก็บไฟล์หลังโพสต์เสร็จ
เมื่อโพสต์ครบแล้ว ให้ย้ายไฟล์ไป Archive:

**PowerShell Command:**
```powershell
# ย้ายโฟลเดอร์วันนี้ไป 03_Posted
Move-Item "02_ReadyToPost\2026-02-07" "03_Posted\2026-02-07" -Force

# หรือย้ายทุกโฟลเดอร์ใน 02_ReadyToPost
Get-ChildItem "02_ReadyToPost" -Directory | ForEach-Object {
    Move-Item $_.FullName "03_Posted\$($_.Name)" -Force
}
```

**หรือบอก Agent:** "ย้ายไฟล์ไป Archive" หรือ "เคลียร์ 02_ReadyToPost"

</details>

---

## ⚡ Quick Commands

| Command | Description |
|---------|-------------|
| `python tools/daily_content_generator.py` | **NEW: One-command automation (Standalone)** |
| `python ../manage.py shopee --mode full` | **NEW: Pipeline architecture (Full Mode)** |

---

## 🎯 Next Steps

1. ✅ Test the new automation script
2. ⏳ Integrate with OpenClaw PM
3. ✅ Add affiliate link conversion (Integrated via Playwright!)
4. ⏳ Add auto-posting to Facebook (optional)
