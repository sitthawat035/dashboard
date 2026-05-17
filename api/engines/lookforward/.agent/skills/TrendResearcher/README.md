# TrendResearcher Usage Guide

**Purpose**: ค้นหาและคัดกรองแนวโน้มเทคโนโลยี (AI, Crypto, Tech) จากแหล่งข้อมูลที่มีความน่าเชื่อถือสูง เพื่อนำไปวิเคราะห์ต่อยอดเป็นเนื้อหาเชิงลึก (Authority Content) สำหรับเพจ **"lookforward"**

---

## 🎯 Target Sources (High-Signal Only)

### AI Research
- **ArXiv** - Latest AI/ML research papers
- **OpenAI Blog** - Official updates and research
- **Google DeepMind Blog** - Cutting-edge AI developments

### Developer Trends
- **GitHub Trending** - Popular repositories and emerging tech
- **Product Hunt** - New tech products (Tech category only)

### Crypto Analysis
- **CoinDesk Research** - In-depth crypto analysis
- **Official Project Whitepapers** - Primary sources
- **X (Twitter)** - Tech-focused crypto accounts only

### Industry News
- **TechCrunch** - Deep Tech coverage
- **Wired** - Technology and policy
- **The Verge** - Tech industry analysis

---

## 🚀 Quick Start

### 1. Run Tech Trend Scanner
```powershell
# Scan high-signal tech sources
python .agent/skills/TrendResearcher/trend_scanner.py

# Specify focus area
python .agent/skills/TrendResearcher/trend_scanner.py --category ai
python .agent/skills/TrendResearcher/trend_scanner.py --category crypto
python .agent/skills/TrendResearcher/trend_scanner.py --category tech

# Custom output directory
python .agent/skills/TrendResearcher/trend_scanner.py --output 01_Research/trends
```

---

## 📄 Output Format

Creates files in `01_Research/trends/YYYY-MM-DD/`:

### 1. `tech_trends.json`
```json
{
  "date": "2026-02-08",
  "category": "AI",
  "trends": [
    {
      "rank": 1,
      "trend_name": "DeepSeek R1 Architecture Analysis",
      "source": "https://arxiv.org/...",
      "source_type": "Research Paper",
      "why_it_matters": "เปลี่ยนโครงสร้างต้นทุน AI training ของโลก",
      "key_facts": [
        "Training cost: $5.6M (vs GPT-4: $100M+)",
        "Open-source architecture",
        "Competitive with GPT-4 on benchmarks"
      ],
      "technical_significance": "high",
      "scraped_at": "2026-02-08T03:00:00"
    }
  ],
  "total_found": 5
}
```

### 2. `trend_report.md`
Human-readable markdown report with:
- Trend name and source
- Why it matters (systemic impact)
- Key technical facts
- Recommended analysis angle

---

## ✅ Features

✅ **High-Signal Sources** - Primary sources only (research papers, official blogs, whitepapers)  
✅ **Quality > Quantity** - Reports "No High-Signal Trends" if nothing meets standards  
✅ **Fact-Focused** - Gathers technical data, statistics, mechanisms  
✅ **Authority-Ready** - Pre-filtered for deep analysis potential  
✅ **Anti-Hype** - Filters out clickbait and price speculation  

---

## 🔍 Scanning Process

### Step 1: Source Filtering
- เลือกเฉพาะข้อมูลที่มีหลักฐานรองรับ หรือมาจากแหล่งข่าวต้นทาง (Primary Sources)
- **Rule**: ข้ามข่าวลือที่ไม่มีที่มาที่ไป หรือข่าวกระแสไวรัลที่ไม่มีคุณค่าเชิงระบบ

### Step 2: Signal Detection
- มองหา "เทคโนโลยีต้นน้ำ" ที่กำลังจะมีผลกระทบในวงกว้าง
- วิเคราะห์ระดับความสำคัญเบื้องต้น (Technical Significance)

### Step 3: Data Gathering
- รวบรวมข้อมูลตัวเลข, สถิติ, หรือกลไกการทำงานเบื้องต้น
- ตรวจสอบความถูกต้องของ Fact ในระดับเริ่มต้น

---

## 🚨 Guardrails

❌ **ห้ามดึงข้อมูลที่เป็นเพียงการปั่นกระแสราคา** (Crypto Price Hype)  
❌ **ห้ามใช้แหล่งข่าวที่เน้นพาดหัว Clickbait** เกินจริง  
❌ **หากไม่พบเทรนด์ที่มีคุณภาพสูงในวันนั้น** ให้รายงานว่า "No High-Signal Trends Found" (Quality > Quantity)

---

## 🔗 Next Steps After Research

Use the output with:
```powershell
# Generate authority content strategy
python .agent/skills/ContentStrategist/strategist.py --trends 01_Research/trends/2026-02-08/tech_trends.json

# Or run full pipeline
python run_pipeline.py --skip-trends --topic "DeepSeek Architecture"
```

---

## 📝 Implementation Notes

**Current Status**: This skill focuses on **high-signal tech sources** for authority content creation.

For production use, ensure:
1. ✅ API access to ArXiv, GitHub API (if needed)
2. ✅ Web scraping for official blogs (OpenAI, DeepMind, etc.)
3. ✅ RSS feeds for TechCrunch, Wired, The Verge
4. ✅ Fact verification against primary sources
5. ✅ Technical significance scoring algorithm

---

**Version**: 2.0 (Authority Edition)  
**Last Updated**: 2026-02-08  
**Alignment**: lookforward Brand (Tech Authority)
