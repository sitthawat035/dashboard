# รายงานวิเคราะห์ปัญหา Anti-bot และแนวทางแก้ไข

## 📋 สรุปปัญหา

Dashboard มีปัญหาการทำงานล้มเหลวเนื่องจากระบบ Anti-bot ของ Shopee ขณะทำการ Scraping ข้อมูลสินค้า 15 รายการเพื่อสร้างไฟล์ CSV ในส่วนของ Shopee Affiliate Search (Tab 2) ซึ่งรับค่า Trend มาจาก Tab 3

---

## 🔍 การวิเคราะห์ระบบปัจจุบัน

### 1. โครงสร้างการทำงานปัจจุบัน

```
Dashboard (Tab 3: Trend) 
    ↓ ส่ง keyword
Dashboard (Tab 2: Shopee Search)
    ↓ เรียก API /api/scrape/shopee
shopee_search_scraper.py
    ↓ ใช้ Playwright + CDP
Chrome Browser (remote debugging port 9222)
    ↓ ติด Anti-bot/Captcha
❌ ล้มเหลว
```

### 2. ไฟล์ที่เกี่ยวข้อง

| ไฟล์ | หน้าที่ | ปัญหา |
|------|---------|-------|
| [`dashboard/server.py`](dashboard/server.py:392) | API endpoint `/api/scrape/shopee` | เรียก scraper แบบ synchronous |
| [`shopee_affiliate/tools/shopee_search_scraper.py`](shopee_affiliate/tools/shopee_search_scraper.py) | ตัว scraping หลัก | ใช้ Playwright ตรวจจับได้ง่าย |
| [`common_shared/browser.py`](common_shared/browser.py) | Browser manager | มี stealth measures แต่ไม่เพียงพอ |
| [`common_shared/stealth_config.py`](common_shared/stealth_config.py) | Stealth configuration | มีอยู่แล้วแต่อาจต้องปรับปรุง |

### 3. จุดอ่อนของระบบปัจจุบัน

1. **Playwright Automation Detection**: แม้จะมี stealth measures แต่ Shopee มีระบบตรวจจับที่ทันสมัย
2. **CDP Connection**: การเชื่อมต่อผ่าน Chrome DevTools Protocol อาจถูกตรวจจับได้
3. **Behavior Pattern**: การ scroll และ extract ข้อมูลแบบ automate มี pattern ที่ตรวจจับได้
4. **No Human Simulation**: ขาดการจำลองพฤติกรรมมนุษย์ เช่น mouse movement, random pauses

---

## 🛠️ Skills ที่มีอยู่

### Skill 1: openclaw-browser (Native Computer Use)

**ที่ตั้ง**: [`shopee_affiliate/.agent/skills/openclaw-browser/SKILL.md`](shopee_affiliate/.agent/skills/openclaw-browser/SKILL.md)

**ความสามารถ**:
- ✅ ควบคุม browser แบบ Native Computer Use (screenshot-based)
- ✅ ใช้ mouse/keyboard เหมือนมนุษย์
- ✅ ไม่ต้องใช้ CSS selectors
- ✅ มี visual verification ทุก action
- ✅ หลบหลีก anti-bot ได้ดีเพราะดูเหมือนการใช้งานจริง

**ข้อจำกัด**:
- ❌ ต้องการ AI ที่สามารถวิเคราะห์ screenshot (เช่น Claude, GPT-4 Vision)
- ❌ ช้ากว่า automation แบบปกติ
- ❌ ต้องมี browser แบบ headed (มีหน้าจอ)

**Workflow**:
```
[รับ Task] → [เปิด/Focus Browser] → [Screenshot] → [วิเคราะห์ UI] → [Action] → [Screenshot ตรวจสอบ] → [Loop หรือ Done]
```

### Skill 2: browser-automation (Playwright)

**ที่ตั้ง**: [`shopee_affiliate/.agent/skills/browser-automation/SKILL.md`](shopee_affiliate/.agent/skills/browser-automation/SKILL.md)

**ความสามารถ**:
- ✅ ใช้ Playwright สำหรับ automation
- ✅ รองรับ form filling, screenshot, scraping
- ✅ มี scripts พร้อมใช้งาน (browse.py, scrape.py, screenshot.py)
- ✅ รองรับ pagination, cookies, custom user-agent

**ข้อจำกัด**:
- ❌ ใช้ Playwright API ที่อาจถูกตรวจจับได้
- ❌ ต้องรู้ CSS selectors

**Scripts ที่มี**:
- `scripts/browse.py` - สำหรับ browsing ทั่วไป
- `scripts/scrape.py` - สำหรับ data extraction
- `scripts/screenshot.py` - สำหรับ capture screenshot
- `scripts/form_fill.py` - สำหรับกรอกฟอร์ม

---

## 📊 เปรียบเทียบแนวทาง

| คุณสมบัติ | ระบบปัจจุบัน | openclaw-browser | browser-automation |
|-----------|--------------|------------------|-------------------|
| Anti-bot Bypass | ❌ อ่อน | ✅ แข็งแกร่ง | ⚠️ ปานกลาง |
| ความเร็ว | ✅ เร็ว | ❌ ช้า | ✅ เร็ว |
| ความซับซ้อน | ⚠️ ปานกลาง | ❌ ซับซ้อน | ✅ ง่าย |
| ต้องการ AI Vision | ❌ ไม่ต้อง | ✅ ต้องการ | ❌ ไม่ต้อง |
| Headless Support | ✅ ได้ | ❌ ต้อง headed | ✅ ได้ |
| Implementation Effort | - | ⚠️ ปานกลาง | ✅ ต่ำ |

---

## 💡 ข้อเสนอแนะ

### แนวทางที่ 1: ปรับปรุง Stealth Measures (แนะนำ - ง่ายที่สุด)

**วิธีการ**: เพิ่มความสามารถ stealth ให้ระบบปัจจุบัน

**ขั้นตอน**:
1. เพิ่ม human-like behavior simulation:
   - Random mouse movements
   - Random scroll patterns
   - Random delays with natural distribution
   - Reading time simulation

2. ปรับปรุง browser fingerprint:
   - ใช้ `BrowserFingerprint` class จาก stealth_config.py
   - Randomize fingerprint ทุกครั้งที่เริ่ม session

3. เพิ่ม request interception:
   - Block tracking scripts
   - Modify headers dynamically

**ตัวอย่างโค้ด**:
```python
# เพิ่มใน shopee_search_scraper.py
from common_shared.stealth_config import BrowserFingerprint, StealthStrategy

async def scrape_with_stealth(keyword: str, max_items: int = 10):
    fingerprint = BrowserFingerprint.random()
    
    async with await create_browser_manager(logger=logger) as browser:
        # Apply stealth
        await browser._apply_stealth(browser.page)
        
        # Human-like navigation
        await human_like_navigate(browser, search_url)
        
        # Random delay before scraping
        await asyncio.sleep(get_random_delay(2000, 5000))
        
        # Human-like scroll
        await human_like_scroll(browser)
```

### แนวทางที่ 2: ใช้ browser-automation Skill (ปานกลาง)

**วิธีการ**: นำ scripts จาก browser-automation skill มาปรับใช้

**ขั้นตอน**:
1. ใช้ `scripts/scrape.py` เป็นฐาน
2. เพิ่ม stealth configuration
3. ใช้ cookies persistence
4. เพิ่ม proxy rotation (ถ้ามี)

**ข้อดี**:
- มี scripts พร้อมใช้งาน
- รองรับ pagination
- รองรับ cookies

### แนวทางที่ 3: ใช้ openclaw-browser Skill (ซับซ้อนที่สุด - แต่มีประสิทธิภาพสูงสุด)

**วิธีการ**: แปลง workflow เป็น Native Computer Use

**ขั้นตอน**:
1. สร้าง AI-powered scraper ที่ใช้ screenshot analysis
2. ใช้ mouse/keyboard control แทน Playwright API
3. ทุก action ต้องมี visual verification

**ข้อดี**:
- หลบหลีก anti-bot ได้ดีที่สุด
- ดูเหมือนการใช้งานจริงที่สุด

**ข้อเสีย**:
- ต้องการ AI ที่มี vision capabilities
- ช้ากว่าวิธีอื่น
- ซับซ้อนในการ implement

---

## 🎯 คำแนะนำสุดท้าย

### ระยะสั้น (ทันที):
1. **เพิ่ม human-like delays** ใน scraping workflow
2. **ปรับปรุง scroll behavior** ให้เหมือนมนุษย์มากขึ้น
3. **เพิ่ม random mouse movements** ก่อน click

### ระยะกลาง:
1. **นำ browser-automation skill** มาปรับใช้
2. **เพิ่ม proxy rotation** (ถ้ามีงบประมาณ)
3. **ใช้ cookies persistence** เพื่อลดการถูกตรวจจับ

### ระยะยาว:
1. **พัฒนา Native Computer Use approach** ตาม openclaw-browser skill
2. **ใช้ AI vision** สำหรับ visual scraping
3. **สร้าง fallback mechanism** เมื่อติด captcha

---

## 📝 ไฟล์ที่ควรแก้ไข

### ไฟล์หลัก:
1. [`shopee_affiliate/tools/shopee_search_scraper.py`](shopee_affiliate/tools/shopee_search_scraper.py) - เพิ่ม stealth measures
2. [`common_shared/browser.py`](common_shared/browser.py) - เพิ่ม human-like behaviors
3. [`common_shared/stealth_config.py`](common_shared/stealth_config.py) - เพิ่ม configuration options

### ไฟล์รอง:
1. [`dashboard/server.py`](dashboard/server.py) - เพิ่ม error handling สำหรับ anti-bot
2. [`shopee_affiliate/scripts/steps/step_load_products.py`](shopee_affiliate/scripts/steps/step_load_products.py) - ปรับปรุง loading logic

---

## 🔗 อ้างอิง

- [openclaw-browser Skill](shopee_affiliate/.agent/skills/openclaw-browser/SKILL.md)
- [browser-automation Skill](shopee_affiliate/.agent/skills/browser-automation/SKILL.md)
- [UI Patterns Reference](shopee_affiliate/.agent/skills/openclaw-browser/ui-patterns.md)
- [Keyboard Shortcuts](shopee_affiliate/.agent/skills/openclaw-browser/keyboard-shortcuts.md)
