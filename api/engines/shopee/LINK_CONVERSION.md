# 🔗 Link Conversion Tools

ชุดเครื่องมือสำหรับการแปลง Shopee links ไป Affiliate links

---

## 📊 Pipeline Overview

```
daily_content_generator.py
    ↓ (สร้าง captions + images)
    ↓
[captions/ ที่มี original Shopee links]
    ↓
extract_links_from_captions.py
    ↓ (สร้าง _links_to_convert.txt)
    ↓
[_links_to_convert.txt - aaaa, bbbb, cccc, dddd]
    ↓
convert_affiliate_links.py (ต้องเปิด Chrome port 9222)
    ↓ (แปลง → affiliate short links)
    ↓
[_converted_links.txt - s.shopee.co.th/XXXX, ...]
    ↓
update_captions_with_converted_links.py
    ↓ (วางลิงค์กลับไปใน captions)
    ↓
[final captions/ ที่มี affiliate links]
```

---

## 🛠️ Tools

### 1️⃣ `extract_links_from_captions.py`
**สร้างไฟล์รวบรวมลิงค์จาก captions**

Extracts Shopee links from all captions in a date folder and creates `_links_to_convert.txt`

**Usage:**
```bash
python tools/extract_links_from_captions.py [date]
```

**Example:**
```bash
python tools/extract_links_from_captions.py 2026-02-21
```

**Output:**
- `data/05_ReadyToPost/2026-02-21/_links_to_convert.txt` (ลิงค์ต่อบรรทัด)

---

### 2️⃣ `convert_affiliate_links.py`
**แปลง Shopee links เป็น Affiliate short links**

Uses Playwright + Chrome DevTools Protocol to convert links

**Requirements:**
1. Chrome/Chromium เปิด:
```bash
chrome.exe --remote-debugging-port=9222
```

2. Login to https://affiliate.shopee.co.th ในหน้า Chrome

**Usage:**
```bash
python tools/convert_affiliate_links.py --file _links_to_convert.txt --output _converted_links.txt
```

**Output:**
- `data/05_ReadyToPost/YYYY-MM-DD/_converted_links.txt`

---

### 3️⃣ `update_captions_with_converted_links.py`
**อัปเดต captions ด้วย affiliate links ที่แปลงแล้ว**

Replaces original Shopee links with converted affiliate links in captions

**Usage:**
```bash
python tools/update_captions_with_converted_links.py [date] --input _converted_links.txt
```

**Example:**
```bash
python tools/update_captions_with_converted_links.py 2026-02-21
```

---

### 4️⃣ `link_conversion_workflow.py` (RECOMMENDED)
**Workflow สมบูรณ์ - รันทั้ง 3 steps พร้อมกัน**

Runs all 3 steps in sequence: extract → convert → update

**Requirements:**
```bash
chrome.exe --remote-debugging-port=9222
```

**Usage:**
```bash
python tools/link_conversion_workflow.py [date]
```

**Example:**
```bash
python tools/link_conversion_workflow.py 2026-02-21
```

---

## 📋 Workflow ทั้งหมด

### ขั้นตอนที่ 1: สร้าง Content (captions + images)
```bash
python tools/daily_content_generator.py
```
Output: `data/05_ReadyToPost/2026-02-21/08.00/`, `12.00/`, `18.00/`, `22.00/`

### ขั้นตอนที่ 2: แปลง Links (เลือก 1 วิธี)

**วิธี A: Automated Workflow (แนะนำ)**
```bash
# เปิด Chrome ก่อน
chrome.exe --remote-debugging-port=9222

# แล้วรันนี้
python tools/link_conversion_workflow.py 2026-02-21
```

**วิธี B: Manual Step by Step**
```bash
# Step 1: Extract
python tools/extract_links_from_captions.py 2026-02-21

# Step 2: Convert (ต้องเปิด Chrome)
python tools/convert_affiliate_links.py --file data/05_ReadyToPost/2026-02-21/_links_to_convert.txt --output data/05_ReadyToPost/2026-02-21/_converted_links.txt

# Step 3: Update
python tools/update_captions_with_converted_links.py 2026-02-21
```

---

## 🚨 Troubleshooting

### ❌ "Chrome not available on port 9222"
```bash
# เปิด Chrome ใหม่
chrome.exe --remote-debugging-port=9222
```

### ❌ "Not logged in to Shopee Affiliate"
1. ไปที่ https://affiliate.shopee.co.th
2. Login ด้วย Shopee account
3. หรือไปที่ https://affiliate.shopee.co.th/offer/custom_link ล่วงหน้า
4. รันสคริปต์อีกครั้ง

### ❌ "_links_to_convert.txt not found"
1. Verify captions มีอยู่ใน `data/05_ReadyToPost/YYYY-MM-DD/HH.MM/caption.txt`
2. รัน `extract_links_from_captions.py` ก่อน

### ⚠️ "No converted link available"
- อาจจำนวน links < 4 ลิงค์
- ลองรัน convert_affiliate_links.py อีกครั้ง

---

## 📂 File Structure After Workflow

```
data/05_ReadyToPost/2026-02-21/
├── 08.00/
│   ├── caption.txt ✓ (updated with affiliate link)
│   └── product_image.webp
├── 12.00/
│   ├── caption.txt ✓ (updated with affiliate link)
│   └── product_image.webp
├── 18.00/
│   ├── caption.txt ✓ (updated with affiliate link)
│   └── product_image.webp
├── 22.00/
│   ├── caption.txt ✓ (updated with affiliate link)
│   └── product_image.webp
├── _links_to_convert.txt (aaaa, bbbb, cccc, dddd)
└── _converted_links.txt (s.shopee.co.th/..., ...)
```

---

## 💡 Quick Reference

| Task | Command |
|------|---------|
| สร้าง content (full) | `python daily_content_generator.py` |
| แปลง links (auto) | `python link_conversion_workflow.py [date]` |
| Extract links เฉพาะ | `python extract_links_from_captions.py [date]` |
| Update captions เฉพาะ | `python update_captions_with_converted_links.py [date]` |

---

**Version:** 2.0  
**Last Updated:** 2026-02-21  
**Status:** Production Ready ✅
