# lookforward - Tech Authority Content System

Automated authority content creation system for deep tech analysis (AI, Crypto, Tech). Built for **"lookforward"** - a tech analysis page focused on building long-term intellectual trust through non-obvious insights and systemic thinking.

---

## 🎯 Mission

**"We do not create noise. We create clarity."**

Build authority through:
- **Depth > Speed**: วิเคราะห์ให้ลึกถึงโครงสร้างระบบ
- **Clarity > Hype**: สร้างความชัดเจน ไม่สร้างความตื่นตระหนก  
- **Insight > News**: ไม่แค่สรุปข่าว แต่บอกว่า "ทำไมมันถึงสำคัญ"

**Current Status**: 36 Followers → Focus on Trust & Authority Growth

---

## 📁 Project Structure

```
lookforward/
├── system_prompt.md          # AI behavior configuration (Authority-focused)
├── brand_guidelines.md       # lookforward voice, style, quality standards
├── README.md                 # This file
├── quick_generate.py         # Lightweight content generator (Direct Gemini API)
├── requirements.txt          # Python dependencies
│
├── data/
│   ├── 01_Research/          # Tech trend research
│   ├── 02_Strategy/          # Content strategies/plans
│   ├── 03_Media/             # Technical visuals & prompts
│   ├── 04_Drafts/            # Content drafts (approved/rejected)
│   ├── 05_Published/         # Published archive
│   ├── 07_Analytics/         # Performance reports
│   ├── 08_Calendar/          # Publishing schedule
│   └── 09_ReadyToPost/       # Clean files ready for Facebook
│
└── scripts/                  # Processing & Orchestration scripts
    ├── run_pipeline_gemini.py     # Main high-authority pipeline (CLI)
    ├── run_strategist_gemini.py   # Strategy-only generation
    ├── pipeline_controller.py     # Pipeline controller class
    ├── get_latest_post.py         # Clipboard helper
    └── steps/                     # Modular pipeline steps
        ├── __init__.py
        ├── base_step.py           # Base step class
        ├── step_strategy.py       # Strategy generation step
        ├── step_content.py        # Content generation step
        ├── step_images.py         # Image prompts step
        └── step_ready_to_post.py  # Ready to post packaging step
```

---

## 🚀 Quick Start

### **1. Full Pipeline (Recommended)**
```bash
# Navigate to project folder
cd d:/MultiContentApp/lookforward

# Run with topic
python scripts/run_pipeline_gemini.py --topic "DeepSeek R1 Architecture Analysis"

# Run with specific mode
python scripts/run_pipeline_gemini.py --mode full --topic "AI Technology Trends"
```

### **2. Pipeline Modes**

| Mode | Description | Use Case |
|------|-------------|----------|
| `full` | Complete pipeline (default) | Full production workflow |
| `quick` | Skip strategy step | Fast content generation |
| `strategy-only` | Generate strategy only | Planning phase |
| `content-only` | Generate content only | Skip strategy |
| `dry-run` | Test without saving | Development/testing |
| `legacy` | Original workflow | Backward compatibility |

### **3. CLI Options**
```bash
python scripts/run_pipeline_gemini.py [OPTIONS]

Options:
  --topic TEXT       Topic for content generation
  --mode MODE        Pipeline mode (full/quick/strategy-only/content-only/dry-run/legacy)
  --step STEP        Run specific step only
  --help             Show help message
```

### **4. Ready-to-Post Output**
Output folder: `data/09_ReadyToPost/[date]/[topic]_[timestamp]/`
- `post.txt` - Thai Content + Hashtags
- `caption.txt` - Engaging Hook/Caption
- `_metadata.json` - Insight Score & Analysis info

---

## 🧩 Pipeline Architecture

### Modular Step System
The pipeline uses a modular step-based architecture:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│  Strategy   │───▶│  Content    │───▶│  Images     │───▶│ ReadyToPost  │
│  (Step 1)   │    │  (Step 2)   │    │  (Step 3)   │    │  (Step 4)    │
└─────────────┘    └─────────────┘    └─────────────┘    └──────────────┘
```

### State Management
- Pipeline state is persisted in `.agent/pipeline_state.json` (Unified State v2.0)
- Resume from any failed step
- Track progress and history

### Error Handling
- Hierarchical error types (AIError, NetworkError, etc.)
- Automatic retry with exponential backoff
- Graceful degradation

---

## 🎙️ Lookforward Studio (Web UI)

A dedicated web interface to manage content and visualize the pipeline.

### **Start the Studio**
```bash
cd d:/MultiContentApp/lookforward
python studio/server.py
```
> **Access:** Open your browser at `http://localhost:5000`

### **Features**
- **Content Feed**: View all "Ready to Post" content
- **Deep Dive**: Click any post to see full details
- **Ignite Analysis**: Trigger new analysis from UI

---

## 🧠 Content Philosophy: Logic Over Noise

### Insight Enforcement Layer (CRITICAL)
Every piece of content must pass through these three gates:

1. **Non-Obvious Requirement**: มุมมองที่คนทั่วไปมองข้าม หรือสิ่งที่คนส่วนใหญ่เข้าใจผิด
2. **Systemic Cause**: อธิบายปัญหาหรือกลไกที่ "โครงสร้างระบบ" ไม่ใช่แค่ปลายเหตุ
3. **Insight Score**: Publish เฉพาะเนื้อหาที่ได้คะแนน **4/5** ขึ้นไป
   - **1-2**: General summary or basic info (**REJECT**)
   - **3**: List-based analysis (**NEEDS WORK**)
   - **4**: Sharp insight connecting systems (**APPROVED**)
   - **5**: Future vision/Non-obvious systemic analysis (**EXCELLENT**)

---

## 📏 Operational Rules (lookforward Standard)

1. **Fact-First**: ข้อมูลต้องแม่นยำและตรวจสอบได้เสมอ
2. **Calm Disrupt**: ใช้ภาษาที่นิ่งแต่เฉียบคม งดใช้ "🚨" หรือคำ Overhype
3. **Follower Conversion**: ท้ายโพสต์ต้องให้เหตุผลเชิงคุณค่าว่าทำไมต้อง Follow
4. **No AI-Speak**: ตัดคำฟุ่มเฟือยและคำทางการที่ดูเป็นหุ่นยนต์ออกทั้งหมด

---

## 📊 Quality Scoring (100 pts)
- **Fact Accuracy (30 pts)**: ข้อมูลถูกต้อง มีแหล่งอ้างอิง
- **Insight Density (30 pts)**: มีข้อมูลที่คนทั่วไปมองข้ามหรือวิเคราะห์ลึก (Insight Score 4-5)
- **Logic Structure (20 pts)**: Update → Breakdown → Impact → Vision
- **No-Hype Integrity (20 pts)**: รักษาความเป็นมืออาชีพ ไม่ใช้คำเว่อ

---

## 🔗 Integration with MultiContentApp

This project is part of the MultiContentApp ecosystem:

- **Dashboard**: Control from unified dashboard at `http://localhost:5000`
- **Shared Modules**: Uses `common_shared/` for AI client, browser automation (Stealth Enabled), state management, error handling
- **Cross-Project**: Works alongside `shopee_affiliate` project

---

## 💡 Pro Tips

1. **Insight Score 4-5 is mandatory** - Don't compromise on authority.
2. **Systemic thinking wins** - Connect dots that others miss.
3. **Calm tone builds trust** - No need to shout or hype.
4. **Look forward, always** - "What's next?" is your signature value.

---

**Version**: 4.2 (Shared Module Anti-Bot Support)  
**Last Updated**: 2026-02-22  
**Status**: Active Production 🚀
**Brand**: lookforward - Tech Authority & Future Strategist
