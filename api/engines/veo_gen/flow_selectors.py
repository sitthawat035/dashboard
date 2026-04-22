# =============================================================================
# flow_selectors.py — Google Flow Labs UI Selectors (CALIBRATED)
# =============================================================================
# อัปเดตจากผลลัพธ์ discover_flow.py เมื่อ 2026-04-21
# ทุก selector เก็บไว้ที่นี่ที่เดียว เวลา Google อัปเดต UI แก้ไฟล์นี้ไฟล์เดียว
# แต่ละ key เป็น list ของ fallback selectors (ลองตัวแรกก่อน ถ้าไม่เจอลองตัวถัดไป)
# =============================================================================

FLOW_URL = "https://labs.google/fx/th/tools/flow"

# --- Main UI Elements ---
SELECTORS = {
    # =========================================================================
    # LANDING PAGE
    # =========================================================================

    # ปุ่มสร้างโปรเจ็กต์ใหม่ (หน้า Landing)
    "new_project_button": [
        "button:has-text('โปรเจ็กต์ใหม่')",
        "button:has-text('add_2โปรเจ็กต์ใหม่')",
        "button:has-text('New project')",
    ],

    # ปุ่มย้อนกลับ
    "back_button": [
        "button:has-text('ย้อนกลับ')",
        "button:has-text('arrow_backย้อนกลับ')",
        "button:has-text('Back')",
    ],

    # =========================================================================
    # PROJECT/CREATE VIEW (หลังกดโปรเจ็กต์ใหม่)
    # =========================================================================

    # ช่องพิมพ์ prompt — เป็น div[role=textbox] ไม่ใช่ textarea!
    "prompt_input": [
        "div[role='textbox']",
        "[role='textbox']",
        "textarea",
        "[contenteditable='true']",
    ],

    # ปุ่มส่ง/สร้าง prompt
    "send_button": [
        "button:has-text('arrow_forwardสร้าง')",
        "button:has-text('สร้าง'):not(:has-text('โปรเจ็กต์'))",
        "button:has-text('Generate')",
        "button:has-text('Create')",
        "button[type='submit']",
    ],

    # ปุ่มเพิ่มสื่อ / อัปโหลดรูป
    "upload_button": [
        "button:has-text('เพิ่มสื่อ')",
        "button:has-text('addเพิ่มสื่อ')",
        "button:has-text('Add media')",
        "button:has-text('Upload')",
    ],

    # hidden file input (จะ appear หลังกดปุ่ม upload)
    "upload_input": [
        "input[type='file']",
        "input[type='file'][accept*='image']",
    ],

    # =========================================================================
    # MODEL SELECTOR
    # =========================================================================

    # ปุ่มเลือกโมเดล (แสดงโมเดลปัจจุบัน)
    "model_selector": [
        "button:has-text('Nano Banana')",
        "button:has-text('Veo')",
        "button:has-text('🍌')",
        "button[id^='radix-']:has-text('Banana')",
        "button[id^='radix-']:has-text('Veo')",
    ],

    # ตัวเลือก: Nano Banana 2 (ใน dropdown/popover)
    "model_option_nano": [
        "div[role='option']:has-text('Nano Banana')",
        "div[role='menuitem']:has-text('Nano Banana')",
        "button:has-text('Nano Banana 2')",
        "li:has-text('Nano Banana')",
        "[data-value*='nano' i]",
    ],

    # ตัวเลือก: Veo 3.1 (ใน dropdown/popover)
    "model_option_veo": [
        "div[role='option']:has-text('Veo')",
        "div[role='menuitem']:has-text('Veo')",
        "button:has-text('Veo 3.1')",
        "button:has-text('Veo')",
        "li:has-text('Veo')",
        "[data-value*='veo' i]",
    ],

    # =========================================================================
    # GENERATION & RESULTS
    # =========================================================================

    # สถานะ loading / generating
    "loading_indicator": [
        "[aria-busy='true']",
        "[role='progressbar']",
        ".loading",
        ".generating",
        "mat-spinner",
    ],

    # ผลลัพธ์รูปภาพ (keyframe)
    "result_image": [
        "img[src*='blob:']",
        "img[src*='generated']",
        ".generated-image img",
        "img[src*='googleusercontent']",
        "img[alt*='Generated']",
    ],

    # ผลลัพธ์วิดีโอ
    "result_video": [
        "video",
        "video[src*='blob:']",
        "video source",
    ],

    # =========================================================================
    # VIDEO CREATION (จากภาพนิ่ง → วิดีโอ)
    # =========================================================================

    # ปุ่ม "เริ่ม" / Start สำหรับสร้างวิดีโอจาก keyframe
    "start_video_button": [
        "button:has-text('เริ่ม')",
        "button:has-text('Start')",
        "button:has-text('play_moviesเครื่องมือสร้างฉาก')",
        "button:has-text('เครื่องมือสร้างฉาก')",
        "button:has-text('Animate')",
        "button:has-text('Create video')",
    ],

    # =========================================================================
    # DOWNLOAD
    # =========================================================================

    "download_button": [
        "button:has-text('ดาวน์โหลด')",
        "button:has-text('Download')",
        "button:has-text('download')",
        "a[download]",
    ],

    # =========================================================================
    # SETTINGS (ถ้ามี)
    # =========================================================================

    "settings_button": [
        "button:has-text('ดูการตั้งค่า')",
        "button:has-text('settings')",
        "button[id^='radix-']:has-text('settings')",
    ],

    "more_options_button": [
        "button:has-text('ตัวเลือกเพิ่มเติม')",
        "button:has-text('more_vert')",
        "button[id^='radix-']:has-text('more_vert')",
    ],

    # Aspect ratio (อาจอยู่ในปุ่ม model selector เช่น "crop_16_9x2")
    "aspect_ratio_916": [
        "button:has-text('9:16')",
        "button:has-text('crop_9_16')",
        "[data-value='9:16']",
    ],
    "aspect_ratio_169": [
        "button:has-text('16:9')",
        "button:has-text('crop_16_9')",
        "[data-value='16:9']",
    ],
}

# --- Helper Functions ---

def get_selector_chain(key: str) -> list[str]:
    """Get the list of fallback selectors for a given key."""
    return SELECTORS.get(key, [])


def get_combined_selector(key: str) -> str:
    """Get all selectors for a key combined with commas (CSS OR)."""
    selectors = SELECTORS.get(key, [])
    return ", ".join(selectors)
