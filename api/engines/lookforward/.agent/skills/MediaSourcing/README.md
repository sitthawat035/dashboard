# MediaSourcing Usage Guide

**Purpose**: จัดหาภาพประกอบที่ช่วยเพิ่มความน่าเชื่อถือและอธิบายเนื้อหาเชิงเทคนิค (AI, Tech, Crypto) โดยเน้นภาพที่ดูเป็น 'ของจริง' และ 'มีคุณค่า' มากกว่าภาพสวยงามทั่วไป สำหรับเพจ **"lookforward"**

---

## 🎯 Core Mission

จัดหาภาพที่:
- **Technical & Real** (ภาพเทคนิคจริง ไม่ใช่ stock photos ทั่วไป)
- **Credible** (เพิ่มความน่าเชื่อถือ)
- **Informative** (อธิบายเนื้อหาได้ชัดเจน)
- **Authority-Aligned** (สอดคล้องกับ brand lookforward)

---

## 🖼️ Visual Standard (lookforward Style)

### ✅ DO (ภาพที่ควรหา):

**Technical Screenshots**
- หน้าจอ Dashboard
- Code Snippets
- หน้าเว็บจริงของโปรเจกต์
- Terminal/CLI outputs

**System Diagrams**
- แผนผังการทำงาน
- Architecture diagrams
- Infographics สรุปสถิติ
- Flowcharts

**Real Use-case**
- ภาพการใช้งานจริงในสภาพแวดล้อมจริง
- Product demos
- Research lab photos

**Minimalist AI Generated**
- Tech Schematic style
- Blueprint aesthetics
- Clean, professional diagrams

### ❌ DON'T (ห้ามใช้เด็ดขาด):

**Generic Stock Photos**
- รูปคนยิ้มเกินจริง
- รูปหุ่นยนต์จับมือกับคน (ดูปลอม)
- ภาพ "business people" ทั่วไป

**Low-Quality Memes**
- มีมที่ลดทอนความน่าเชื่อถือ
- ภาพตลกที่ไม่เกี่ยวข้อง

**Irrelevant Images**
- ภาพที่ไม่เกี่ยวข้องกับเนื้อหาเชิงเทคนิค
- ภาพแค่สวยแต่ไม่มีคุณค่า

---

## 🚀 Quick Start

### 1. Source Technical Visuals
```powershell
# From content strategy
python .agent/skills/MediaSourcing/media_downloader.py --strategy 02_Strategy/content_plans/2026-02-08/deepseek_architecture.md

# Direct search for technical visuals
python .agent/skills/MediaSourcing/media_downloader.py --keywords "AI architecture diagram" --type technical

# Screenshot from official source
python .agent/skills/MediaSourcing/media_downloader.py --url https://github.com/deepseek-ai/DeepSeek-R1 --type screenshot
```

---

## 🛠️ Sourcing Process

### Step 1: Visual Identification
- วิเคราะห์จาก Content Draft ว่าประเด็นไหนที่ต้องการภาพประกอบเพื่อ "พิสูจน์" หรือ "อธิบาย" ให้เห็นภาพชัดขึ้น

**Example:**
```
Content: "DeepSeek training cost: $5.6M vs GPT-4: $100M+"
Visual Need: Cost comparison chart/infographic
```

### Step 2: Source Selection

**Priority Order:**
1. **Official Assets** (highest priority)
   - GitHub Repo images
   - Project documentation
   - Official blog posts
   - Research paper figures

2. **Research Sources**
   - ArXiv paper diagrams
   - Academic publications
   - Technical whitepapers

3. **Technical Stock** (last resort)
   - Unsplash (tech category)
   - Pexels (technology)
   - Only if truly technical-looking

### Step 3: Optimization
- ตรวจสอบความคมชัดและสัดส่วนที่เหมาะสมกับ Platform
- เขียน **Alt Text** หรือคำอธิบายภาพที่เสริมความเข้าใจเชิงเทคนิค

---

## 📄 Output Format

Creates files in `03_Media/YYYY-MM-DD/[topic]/`:

```
03_Media/2026-02-08/deepseek_architecture/
├── architecture_diagram.png          # Official diagram from paper
├── cost_comparison_chart.png         # Generated infographic
├── benchmark_results_screenshot.png  # Screenshot from research
├── metadata.json                     # Source attribution
└── visual_summary.md                 # Usage guide
```

### metadata.json
```json
{
  "topic": "DeepSeek R1 Architecture",
  "date": "2026-02-08",
  "visuals": [
    {
      "filename": "architecture_diagram.png",
      "type": "technical_diagram",
      "source": "https://arxiv.org/...",
      "source_type": "research_paper",
      "license": "CC BY 4.0",
      "alt_text": "DeepSeek R1 MoE architecture diagram showing expert routing",
      "usage": "Explain technical mechanism"
    },
    {
      "filename": "cost_comparison_chart.png",
      "type": "infographic",
      "source": "generated",
      "tool": "matplotlib",
      "alt_text": "Training cost comparison: DeepSeek $5.6M vs GPT-4 $100M+",
      "usage": "Highlight cost efficiency"
    }
  ]
}
```

### visual_summary.md
```markdown
# Visual Assets: DeepSeek R1 Architecture

## 1. Architecture Diagram
**File**: `architecture_diagram.png`  
**Usage**: Explain MoE (Mixture of Experts) mechanism  
**Alt Text**: "DeepSeek R1 MoE architecture diagram showing expert routing"  
**Source**: ArXiv research paper (CC BY 4.0)

## 2. Cost Comparison Chart
**File**: `cost_comparison_chart.png`  
**Usage**: Highlight training cost efficiency  
**Alt Text**: "Training cost comparison: DeepSeek $5.6M vs GPT-4 $100M+"  
**Source**: Generated from research data

## 3. Benchmark Results Screenshot
**File**: `benchmark_results_screenshot.png`  
**Usage**: Prove competitive performance  
**Alt Text**: "DeepSeek R1 benchmark scores on MMLU and HumanEval"  
**Source**: Official GitHub repository
```

---

## ✅ Quality Checklist

Before approving visual:

- [ ] ภาพนี้ช่วยอธิบายเนื้อหาให้เข้าใจง่ายขึ้นใช่หรือไม่?
- [ ] ภาพนี้ดูน่าเชื่อถือและไม่ดูเป็นภาพ Stock ใช่หรือไม่?
- [ ] ภาพมีความเกี่ยวข้องกับข้อมูลตัวเลขหรือข้อเท็จจริงในโพสต์หรือไม่?
- [ ] มี Alt Text ที่อธิบายชัดเจนหรือไม่?
- [ ] มีการระบุแหล่งที่มาและ license หรือไม่?

---

## 🎨 Visual Types by Content

| Content Type | Recommended Visual |
|--------------|-------------------|
| **AI Research** | Architecture diagrams, benchmark charts |
| **Crypto Analysis** | Price charts, blockchain diagrams |
| **Tech Products** | Product screenshots, UI/UX demos |
| **Industry Trends** | Infographics, statistical charts |
| **Technical Tutorials** | Code snippets, terminal screenshots |

---

## 🔗 Recommended Sources

### Official Project Sources
- **GitHub** - Repository images, diagrams
- **ArXiv** - Research paper figures
- **Official Blogs** - OpenAI, DeepMind, etc.
- **Project Docs** - Technical documentation

### Technical Stock (Use Sparingly)
- **Unsplash** - Technology category only
- **Pexels** - Tech/coding category
- **Pixabay** - Technical illustrations

### Tools for Creating Visuals
- **Matplotlib/Plotly** - Data visualization
- **Excalidraw** - Technical diagrams
- **Figma** - Infographics
- **Carbon** - Code screenshots

---

## 📥 Input Files

1. **Strategy**: `02_Strategy/content_plans/YYYY-MM-DD_[topic].md`
   - Contains: media requirements, keywords, visual needs

---

## 🔗 Next Steps After Sourcing

Use the visuals with:
```powershell
# Generate content with media references
python .agent/skills/ContentWriter/writer.py --strategy path/to/strategy.md --media 03_Media/2026-02-08/deepseek_architecture/

# Or run full pipeline
python run_pipeline.py --skip-trends --topic "DeepSeek Architecture"
```

---

## 💡 Pro Tips

1. **Official sources first** - Always check project repos/docs
2. **Technical > Pretty** - Credibility over aesthetics
3. **Alt text matters** - Improves accessibility and SEO
4. **Attribute properly** - Respect licenses and credit sources
5. **Create when needed** - Don't settle for poor stock photos

---

**Version**: 2.0 (Authority Edition)  
**Last Updated**: 2026-02-08  
**Alignment**: lookforward Brand (Tech Authority)
