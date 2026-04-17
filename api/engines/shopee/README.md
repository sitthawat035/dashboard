# 🛍️ Shopee Affiliate Automation (Friend Style)

โปรเจกต์ทำคอนเทนต์ "เพื่อนสาวป้ายยา" แบบอัตโนมัติ! 
เปลี่ยนจากการนั่งเขียนเอง เป็นการใช้ AI ช่วยคัดของดี + เขียนแคปชั่น + จัดการลิงก์ให้เสร็จสรรพ!

---

## 🚀 Quick Start

### **Step 1: เตรียมสินค้า (Input)**
เลือกได้ 2 วิธี:
1. **Auto (แนะนำ):** ใช้ Extension หรือระบบ Scraper แบบอัตโนมัติ (พร้อม Anti-bot Bypass หลบหลีก Captcha ทะลุทะลวงด้วย Bezier Curves) -> Save เป็นไฟล์ `.csv` ไว้ที่ `data/00_ScrapedData/`
2. **Manual:** ถ้าไม่มี CSV ให้กรอกรายชื่อสินค้าลงใน `product_input_template.md`

### **Step 2: รัน AI สร้างคอนเทนต์**
ตอนนี้โปรเจกต์ถูกรวบรวมไว้ที่ Root แล้ว คุณสามารถรันสคริปต์ได้จากที่โฟลเดอร์นอกสุด `MultiContentApp` ได้เลย:

```bash
# กลับไปที่หน้า Root ของโปรเจกต์
cd d:/MultiContentApp/

# รัน Pipeline ข้ามไปจนจบในคำสั่งเดียว (ใช้ script อัตโนมัติที่เพิ่งทำ)
python manage.py shopee --mode full --count 4 --max-price 500

# โหมดอื่นๆ:
# Quick mode (ไม่ต้องโหลดรูป)
python manage.py shopee --mode quick --count 4

# เฉพาะสร้างคอนเทนต์
python manage.py shopee --mode content-only

# จัดการแค่ Link
python manage.py shopee --mode links-only
```

### **Pipeline Modes**

| Mode | Description | Use Case |
|------|-------------|----------|
| `legacy` | Original workflow (default) | Backward compatibility |
| `full` | Complete pipeline + state | Production with tracking |
| `quick` | Skip image download | Fast content generation |
| `content-only` | Generate content only | Skip link conversion |
| `links-only` | Convert links only | Update affiliate links |
| `dry-run` | Test without saving | Development/testing |

### **CLI Options**
```bash
python manage.py shopee [OPTIONS]

Options:
  --mode MODE        Pipeline mode (legacy/full/quick/content-only/links-only/dry-run)
  --count N          Number of products to process (default: 4)
  --max-price PRICE  Maximum price filter (default: 500)
  --help             Show help message
```

### **Step 3: แปลงลิงก์ (Auto แบบใหม่!)**
ระบบจะแปลงลิงก์อัตโนมัติด้วย **Playwright** ตอนนี้ไม่ต้องวางลิงก์เองแบบ Manual อีกแล้ว!
1. แต่กรุณาเปิดหน้าต่าง Chrome Debugging ทิ้งไว้ที่ Port 9222 โดยรันคำสั่ง `chrome.exe --remote-debugging-port=9222` ไว้
2. Login Shopee Affiliate ทิ้งไว้
3. ระบบจะทำงานและสร้าง Short Link แบบ `s.shopee.co.th/...` ยัดลงไปในแคปชั่นตรงๆ เลย!

---

## 📁 Project Structure

```
shopee_affiliate/
├── README.md                 # คู่มือตัวนี้
├── system_prompt.md          # AI behavior configuration
├── WORKFLOW.md               # Detailed workflow และ Automation Guides
│
├── data/
│   ├── 00_ScrapedData/       # CSV files from extension
│   ├── 03_Posted/            # Archive of posted content
│   └── 05_ReadyToPost/       # Final output ready for posting (Updated Path)
│
├── scripts/                  # Processing scripts หลัก
│   ├── run_affiliate_pipeline.py  # Main pipeline (ถูกเรียกจาก manage.py ที่ด้านนอก)
│   ├── pipeline_controller.py     # Pipeline controller class
│   └── steps/                     # Modular pipeline steps
│       ├── __init__.py
│       ├── base_step.py           # Base step class
│       ├── step_load_products.py  # Load products from CSV
│       ├── step_select_products.py # AI product selection
│       ├── step_generate_content.py # Content generation
│       ├── step_download_images.py # Image download
│       ├── step_convert_links.py   # Link conversion (via Playwright)
│       └── step_ready_to_post.py   # Ready to post packaging
└── tools/
    ├── daily_content_generator.py # ตัวสร้างโพสท์รายวันตัวใหม่
    └── convert_affiliate_links.py # Core ระบบบอทแปลงลิงก์ Playwright
```

---

## 🧩 Pipeline Architecture

### Modular Step System
```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ LoadProducts │───▶│SelectProducts│───▶│GenerateContent│───▶│DownloadImages│
│   (Step 1)   │    │   (Step 2)   │    │   (Step 3)   │    │   (Step 4)   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                  │
                                                                  ▼
                                                         ┌──────────────┐
                                                         │ ConvertLinks │
                                                         │   (Step 5)   │
                                                         └──────────────┘
                                                                  │
                                                                  ▼
                                                         ┌──────────────┐
                                                         │ ReadyToPost  │
                                                         │   (Step 6)   │
                                                         └──────────────┘
```

### State Management
- Pipeline state persisted in `.agent/pipeline_state.json` (Unified State v2.0)
- Resume from any failed step
- Track progress and history

---

## 📂 โครงสร้าง Output

ใน `data/05_ReadyToPost/[Date]/` จะมีโฟลเดอร์ย่อยตามเวลา:

- 📂 `0800_ชื่อสินค้าA`
  - `post.txt` (แคปชั่น + Hashtag + Link พร้อมโพสต์!)
  - `caption.txt` (เฉพาะแคปชั่น)
  - `link.txt` (เฉพาะลิงก์)
- 📂 `1200_ชื่อสินค้าB`
...

---

## 🎨 Tone & Style
- **Personality:** เพื่อนสาวขี้เม้าท์, จริงใจ, ตลก, กันเอง
- **Keywords:** "แกรรร", "คือดีย์", "ทุบ!", "ตำด่วน", "555+"
- **Emoji:** 🤣✨🔥🛍️💖

---

## 🔗 Integration with MultiContentApp

This project is part of the MultiContentApp ecosystem:

- **Dashboard**: Control from unified dashboard at `http://localhost:5000`
- **Shared Modules**: Uses `common_shared/` for AI client, browser automation (with Stealth & Anti-bot features), state management, error handling
- **Cross-Project**: Works alongside `lookforward` project

---

## 🛠️ Troubleshooting
- **หาไฟล์ CSV ไม่เจอ?**: เช็คว่าไฟล์อยู่ใน `data/00_ScrapedData/` หรือยัง (สกุล .csv)
- **Error Shared Lib?**: เช็คว่าโฟลเดอร์ `common_shared` อยู่ที่ Workspace Root
- **ลิงก์ไม่เปลี่ยน?**: ย้ำว่าต้องวางลิงก์ใหม่ใน `_paste_converted_links_here.txt`

---

**Version**: 2.3 (Shopee Advanced Anti-Bot Bypass & Resilience)  
**Last Updated**: 2026-02-22  
**Status**: Active Production 🚀

*Happy Posting! 💸*
