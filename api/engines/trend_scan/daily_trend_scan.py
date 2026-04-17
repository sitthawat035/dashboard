"""
Smart Daily Trend Scan  (v2 — Multi-Niche)
==========================================

Improvements over v1:
  ✅ Rotating query pool — ไม่ยิง query เดิมทุกวัน
  ✅ TrendSelector — track history, velocity bonus, blacklist, diversity
  ✅ History injection ใน AI prompt — AI รู้ว่าเลือกอะไรไปแล้ว
  ✅ freshness=pd (past day) สำหรับทุก query — บังคับให้เป็นของใหม่จริงๆ
  ✅ --niche flag — เลือก niche ได้ หรือใส่ custom description
"""

import sys
import json
import os
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load env vars before imports
root_dir   = Path(__file__).resolve().parent
engines_dir = root_dir.parent
load_dotenv(engines_dir / "lookforward/.env")

sys.path.insert(0, str(engines_dir))

from common.search_client import create_search_client
from common.ai_client import create_ai_client
from common.trend_selector import TrendSelector
from common.utils import print_header, print_success, print_info, setup_logger

logger = setup_logger("DailyTrendScan")


# ─── Niche Profiles ───────────────────────────────────────────────────────────
# Each profile: list of rotating search queries (content queries + viral product queries)
NICHE_PROFILES = {

    "tech": {
        "label": "🤖 Tech & AI",
        "content_queries": [
            "latest AI agent autonomous 2026 breakthrough news",
            "new large language model release 2026 announcement",
            "humanoid robot news today 2026",
            "AI startup funding Series A B 2026 breaking",
            "deepseek openai anthropic google gemini news today",
            "EV electric vehicle autonomous driving news 2026",
            "crypto bitcoin ethereum regulation news today",
            "semiconductor chip AI hardware breakthrough 2026",
            "biotech healthtech AI drug discovery news today",
            "space tech SpaceX satellite news 2026",
            "AI in education healthcare finance 2026 news",
            "open source AI model launched released today",
            "tech regulation AI policy government 2026 news",
            "quantum computing cybersecurity 2026 breakthrough",
        ],
        "viral_queries": [
            "viral gadget TikTok Thailand 2026 trending",
            "top selling gadget Amazon Thailand trending today",
            "mini gadget เครื่องใช้ไฟฟ้า ขายดี tiktok ล่าสุด",
            "gaming peripheral accessories trending 2026 Thailand",
            "smart home device viral shopee trend 2026",
            "tech accessory viral twitter pantip week",
            "power bank earphone ขายดี shopee trend 2026",
            "fitness tracker smartwatch trend 2026 viral",
            "eco friendly tech product trend 2026 viral",
            "portable device charging viral trend 2026",
        ],
        "ai_persona": "Trend Analyst ผู้เชี่ยวชาญด้าน Tech และสินค้า Gadget Viral ในไทย",
    },

    "finance": {
        "label": "💰 Finance & Investment",
        "content_queries": [
            "stock market crash rally news today 2026",
            "SET index หุ้นไทย วันนี้ แนวโน้ม",
            "gold price forecast 2026 today breaking",
            "crypto DeFi altcoin news today 2026",
            "Thailand economy GDP inflation news 2026",
            "interest rate central bank news today 2026",
            "IPO หุ้น ไทย น่าลงทุน ข่าว ล่าสุด",
            "real estate investment trend Thailand 2026",
            "forex ค่าเงิน บาท ดอลลาร์ today 2026",
            "Warren Buffett billionaire investment news 2026",
            "mutual fund กองทุน trend today 2026",
            "global recession risk 2026 economy news",
        ],
        "viral_queries": [
            "ลงทุน passive income viral pantip 2026",
            "บัตรเครดิต สะสมแต้ม trend 2026 viral",
            "ประกันชีวิต สุขภาพ ขายดี viral 2026",
            "แอป trading หุ้น viral review 2026",
            "คอร์สเรียน เงิน ลงทุน viral tiktok 2026",
            "กองทุน ETF SSF RMF ดี trend 2026",
            "หนังสือ การเงิน ขายดี 2026 pantip",
            "บ้าน ที่ดิน ราคา trend viral 2026",
        ],
        "ai_persona": "Trend Analyst ผู้เชี่ยวชาญด้านการเงิน การลงทุน และตลาดหุ้นไทย",
    },

    "lifestyle": {
        "label": "✨ Lifestyle & Wellness",
        "content_queries": [
            "wellness trend 2026 mental health viral news",
            "travel destination trending Thailand Southeast Asia 2026",
            "food trend restaurant viral 2026 news",
            "fashion trend 2026 viral outfit style",
            "minimalist lifestyle trend viral 2026",
            "digital nomad remote work lifestyle trend 2026",
            "self-care morning routine viral tiktok 2026",
            "sustainable eco living trend 2026 news",
            "relationship dating app trend Thailand 2026",
            "home decor interior design viral 2026",
        ],
        "viral_queries": [
            "ของตกแต่งบ้าน minimalist viral shopee 2026",
            "กระเป๋า เสื้อผ้า trend viral tiktok thailand",
            "อาหารเสริม วิตามิน viral pantip 2026",
            "เครื่องออกกำลังกาย ขายดี shopee 2026",
            "ของใช้ในบ้าน smart viral tiktok 2026",
            "กระบอกน้ำ แก้วน้ำ viral trend 2026",
            "ผ้าคลุมโซฟา ผ้าม่าน trend shopee 2026",
            "เครื่องมือ ทำความสะอาด viral tiktok 2026",
        ],
        "ai_persona": "Trend Analyst ผู้เชี่ยวชาญด้าน Lifestyle ความเป็นอยู่ และ Wellness ในไทย",
    },

    "beauty": {
        "label": "💄 Beauty & Skincare",
        "content_queries": [
            "skincare trend 2026 viral ingredient news",
            "korean beauty kbeauty trend 2026 new product",
            "sunscreen SPF viral dermatologist 2026 news",
            "cruelty free organic beauty trend 2026",
            "tiktok skincare routine viral 2026 today",
            "anti-aging retinol peptide trend product 2026",
            "japanese beauty japandi skincare viral 2026",
            "makeup trend foundation lipstick viral 2026",
            "hair care scalp treatment trend 2026 viral",
            "beauty device LED mask tool viral 2026",
        ],
        "viral_queries": [
            "สกินแคร์ ราคาถูก ฟังก์ชันเทพ สิว ฝ้า trend ใหม่",
            "korean skincare trend viral 2026 new product",
            "ครีมกันแดด ราคาดี viral tiktok pantip 2026",
            "เซรั่ม วิตามินซี viral shopee 2026",
            "มาสก์หน้า sheet mask viral tiktok 2026",
            "ลิปสติก ลิปบาล์ม viral trend 2026",
            "โทนเนอร์ มอยเจอไรเซอร์ ขายดี shopee 2026",
            "น้ำหอม perfume viral ไทย trend 2026",
        ],
        "ai_persona": "Trend Analyst ผู้เชี่ยวชาญด้าน Beauty Skincare และเครื่องสำอางในไทย",
    },

    "food": {
        "label": "🍜 Food & Restaurant",
        "content_queries": [
            "food trend viral tiktok restaurant 2026 news",
            "ร้านอาหาร เปิดใหม่ กรุงเทพ viral 2026",
            "street food viral thailand 2026 trend",
            "plant based vegan food trend Thailand 2026",
            "cafe coffee trend Bangkok viral 2026",
            "dessert viral tiktok thailand 2026 trending",
            "อาหารไทย fusion ร้านใหม่ michelin 2026",
            "delivery app grab food panda trend 2026",
            "superfood functional food trend 2026 news",
            "bakery bread sourdough viral trend 2026",
        ],
        "viral_queries": [
            "อาหาร viral tiktok pantip shopee สั่งออนไลน์",
            "ขนม ของกิน ขายดี shopee lazada 2026",
            "ชา กาแฟ ดริป viral trend 2026",
            "อาหารสุขภาพ low calorie viral 2026",
            "เครื่องปรุง seasoning viral recipe tiktok 2026",
            "ผลไม้ อบแห้ง snack healthy viral 2026",
            "ขนมไทย โบราณ viral tiktok 2026",
            "protein shake supplement ออกกำลังกาย 2026",
        ],
        "ai_persona": "Trend Analyst ผู้เชี่ยวชาญด้านอาหาร ร้านอาหาร และ Food Trend ในไทย",
    },

    "real-estate": {
        "label": "🏠 Real Estate",
        "content_queries": [
            "คอนโด บ้าน ราคา trend ไทย 2026 ข่าว",
            "real estate Bangkok property market 2026 news",
            "interest rate mortgage home loan Thailand 2026",
            "new condo project launch Bangkok 2026 news",
            "property investment yield rental Thailand 2026",
            "ที่ดิน ราคา เพิ่ม ลด trend 2026",
            "EEC อีอีซี โครงการ อสังหา 2026 ข่าว",
            "smart city development Thailand 2026 news",
            "proptech real estate technology Thailand 2026",
            "foreign property investment Thailand 2026 update",
        ],
        "viral_queries": [
            "บ้านมือสอง ราคาดี review viral 2026",
            "คอนโด ราคาถูก รีวิว pantip 2026",
            "เฟอร์นิเจอร์ ตกแต่งบ้าน viral shopee 2026",
            "ซ่อมบ้าน DIY viral tiktok 2026",
            "ผ้าคลุม โซฟา พรม viral ขายดี 2026",
            "กล้อง วงจรปิด smart home viral 2026",
            "airbnb เช่า ลงทุน trend 2026 pantip",
            "โซลาร์เซลล์ ติดตั้ง ราคา ดี trend 2026",
        ],
        "ai_persona": "Trend Analyst ผู้เชี่ยวชาญด้านอสังหาริมทรัพย์และตลาดบ้าน-คอนโดไทย",
    },

    "health": {
        "label": "🏥 Health & Medical",
        "content_queries": [
            "health breakthrough medical news 2026 today",
            "longevity anti-aging research news 2026",
            "mental health depression anxiety trend news 2026",
            "weight loss GLP-1 Ozempic news 2026 today",
            "cancer treatment AI diagnostic news 2026",
            "สุขภาพ โรค ป้องกัน รักษา ข่าว ล่าสุด 2026",
            "wearable health device monitor trend 2026",
            "supplement probiotic gut health trend 2026 news",
            "Thailand public health policy news 2026",
            "genome DNA personalized medicine news 2026",
        ],
        "viral_queries": [
            "อาหารเสริม วิตามิน viral pantip shopee 2026",
            "เครื่องวัดสุขภาพ ความดัน น้ำตาล viral 2026",
            "โยคะ pilates gym อุปกรณ์ viral tiktok 2026",
            "ยา สมุนไพร viral review pantip 2026",
            "นอนไม่หลับ เครื่องช่วย viral 2026",
            "น้ำมัน ซีบีดี CBD trend ไทย 2026",
            "คอลลาเจน โปรตีน ขายดี shopee 2026",
            "maske หน้ากาก อนามัย viral trend 2026",
        ],
        "ai_persona": "Trend Analyst ผู้เชี่ยวชาญด้านสุขภาพ การแพทย์ และ Wellness ในไทย",
    },
}


def _pick_queries(profile: dict) -> tuple[str, str]:
    """Pick today's queries using day-of-year rotation within the profile."""
    doy = datetime.now().timetuple().tm_yday
    content_queries = profile["content_queries"]
    viral_queries   = profile["viral_queries"]
    content_q = content_queries[doy % len(content_queries)]
    viral_q   = viral_queries[doy % len(viral_queries)]
    return content_q, viral_q


def scan_daily_trends(niche: str = "tech", custom_niche: str = "") -> dict | None:
    search_client = create_search_client()
    ai_client     = create_ai_client()
    selector      = TrendSelector()

    # ── Resolve profile ──────────────────────────────────────────────────────
    if custom_niche:
        # Build an on-the-fly profile from the custom description
        label = f"🔍 Custom: {custom_niche}"
        profile = {
            "label": label,
            "content_queries": [
                f"{custom_niche} news today 2026 breaking",
                f"{custom_niche} trend viral 2026 announcement",
                f"latest {custom_niche} update 2026",
                f"{custom_niche} Thailand news today",
            ],
            "viral_queries": [
                f"{custom_niche} product viral shopee tiktok 2026",
                f"{custom_niche} ขายดี pantip viral 2026",
                f"{custom_niche} trending today Thailand 2026",
            ],
            "ai_persona": f"Trend Analyst ผู้เชี่ยวชาญด้าน {custom_niche} ในตลาดไทย",
        }
    else:
        profile = NICHE_PROFILES.get(niche, NICHE_PROFILES["tech"])
        label   = profile["label"]

    print_header(f"🌐 Smart Daily Trend Scan — Niche: {label}")

    # ── Pick rotating queries ────────────────────────────────────────────────
    content_query, viral_query = _pick_queries(profile)
    today = datetime.now().strftime("%Y-%m-%d")

    print_info(f"📅 วันที่: {today}")
    print_info(f"🔍 Content Query: {content_query}")
    print_info(f"🛍️  Viral Query  : {viral_query}")

    # ── Search ───────────────────────────────────────────────────────────────
    print_info("กำลังค้นหาข่าวใหม่...")
    content_results = search_client.search(content_query, count=7, freshness="pd")

    print_info("กำลังค้นหาสินค้า Viral...")
    viral_results = search_client.search(viral_query, count=7, freshness="pw")

    # ── Build AI prompt ──────────────────────────────────────────────────────
    history_summary  = selector.get_history_summary()
    research_summary = f"NEWS ({label} — ใหม่วันนี้):\n" + "\n".join(
        [f"- {r['title']} | {r.get('url', '')}" for r in content_results]
    )
    research_summary += "\n\nVIRAL / PRODUCT NEWS (สัปดาห์นี้):\n" + "\n".join(
        [f"- {r['title']}" for r in viral_results]
    )

    prompt = f"""
คุณคือ {profile['ai_persona']}

ข้อมูลข่าวล่าสุดวันนี้ ({today}):
{research_summary}

---
⚠️ ประวัติ Topic ที่เลือกไปแล้วล่าสุด (ห้ามเลือกซ้ำ!):
{history_summary}

---
กฎ:
1. วิเคราะห์เฉพาะจากข้อมูลข่าวที่ให้มา ไม่ hallucinate
2. ห้ามเลือก topic/keyword ที่ปรากฏในประวัติ (ดูจาก [วันที่] ด้านบน)
3. เน้น **ความใหม่** (breaking news ในวันนี้ มากกว่า trend สัปดาห์เก่า)
4. ตอบเป็นภาษาไทย (ยกเว้นชื่อเฉพาะ)

เลือก Lookforward 5 หัวข้อ และ Viral Keywords 5 หมวด ที่ **แตกต่างจากที่เลือกไปแล้ว**:

ตอบเป็น JSON เท่านั้น (ไม่มี markdown):
{{
  "lookforward_topics": [
    {{"topic": "หัวข้อบทความ", "reason": "เหตุผลสั้นๆ ว่าทำไมวันนี้ถึงน่าเขียน"}}
  ],
  "shopee_viral": [
    {{"keyword": "คำค้นหาสินค้าภาษาไทย", "trend_score": 1-10, "reason": "เหตุผลสั้นๆ"}}
  ]
}}
"""

    # ── AI Analysis ──────────────────────────────────────────────────────────
    print_info("AI กำลังวิเคราะห์ trend...")
    try:
        response = ai_client.generate(
            prompt, system=profile["ai_persona"]
        )
        clean = response.strip()
        for fence in ["```json", "```JSON", "```"]:
            clean = clean.replace(fence, "")
        data = json.loads(clean.strip())
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return None

    # ── Smart Filtering with TrendSelector ───────────────────────────────────
    print_info("🎯 กำลัง filter + rank ด้วย TrendSelector...")

    raw_topics = data.get("lookforward_topics", [])
    raw_shopee = data.get("shopee_viral", [])

    best_topics = selector.filter_and_rank(raw_topics, kind="lookforward", top_n=3)
    best_shopee = selector.filter_and_rank(raw_shopee, kind="shopee", top_n=3)

    selector.mark_selected(best_topics, kind="lookforward")
    selector.mark_selected(best_shopee, kind="shopee")

    # ── Build final output ───────────────────────────────────────────────────
    result = {
        "date":               today,
        "niche":              niche if not custom_niche else f"custom:{custom_niche}",
        "niche_label":        label,
        "content_query_used": content_query,
        "viral_query_used":   viral_query,
        "lookforward_topics": best_topics,
        "shopee_viral":       best_shopee,
        "raw_candidates": {
            "lookforward": raw_topics,
            "shopee":      raw_shopee,
        },
    }

    # Save latest_trends.json (backward compat)
    latest_path = root_dir / "latest_trends.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # ── Print summary ────────────────────────────────────────────────────────
    print_success(f"\n✅ Trend Scan เสร็จสิ้น! ({today}) — Niche: {label}")

    print_info("\n🔮 Lookforward Topics (filtered):")
    for t in best_topics:
        print_info(f"  ✨ {t['topic']}")
        print_info(f"     → {t.get('reason', '')}")

    print_info("\n🛍️ Viral Keywords (filtered):")
    for v in best_shopee:
        score = v.get("trend_score", "?")
        print_info(f"  🔥 {v['keyword']} (score: {score}) — {v.get('reason', '')}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Smart Daily Trend Scan — scans trending content and viral products"
    )
    parser.add_argument(
        "--niche",
        choices=list(NICHE_PROFILES.keys()),
        default="tech",
        help=f"Niche to scan. Options: {', '.join(NICHE_PROFILES.keys())} (default: tech)",
    )
    parser.add_argument(
        "--custom-niche",
        metavar="DESCRIPTION",
        default="",
        help="Custom niche description (overrides --niche). e.g. 'ธุรกิจ SME ไทย'",
    )
    args = parser.parse_args()
    scan_daily_trends(niche=args.niche, custom_niche=args.custom_niche)


if __name__ == "__main__":
    main()
