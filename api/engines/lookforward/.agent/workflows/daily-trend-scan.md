---
description: Scan high-signal tech sources for AI, Crypto, and Tech innovations daily
---

# Daily Tech Trend Scan Workflow (lookforward Edition)

Execute daily automated high-signal research from authoritative tech sources.

## 🎯 Objective
Identify 1-3 high-signal tech trends with systemic significance to fuel authority content creation.

**Philosophy**: Quality > Quantity - We scan for depth, not volume.

## 📋 Steps

### 1. Prepare Environment

```powershell
# No Chrome CDP needed - we use AI-powered research
# Ensure AI client is configured (.env file)
```

// turbo
### 2. Run TrendResearcher Skill

```powershell
# Invoke the TrendResearcher skill
Write-Host "📡 Scanning high-signal tech sources..."
```

The agent will:
- Scan authoritative sources (ArXiv, OpenAI Blog, DeepMind, GitHub Trending, etc.)
- Filter for technical depth and systemic significance
- Reject clickbait and price speculation
- Output to: `01_Research/trends/YYYY-MM-DD/daily_tech_trends.md`

**Target Sources**:
- **AI Research**: ArXiv, OpenAI Blog, Google DeepMind Blog
- **Developer Trends**: GitHub Trending, Product Hunt (Tech category)
- **Crypto Analysis**: CoinDesk Research, Official Whitepapers
- **Industry News**: TechCrunch (Deep Tech), Wired, The Verge

### 3. Verify Output

Check that file was created:
- `01_Research/trends/YYYY-MM-DD/daily_tech_trends.md`

### 4. Quick Review

Open the tech trends report:
```powershell
# View tech trends
code "01_Research/trends/$(Get-Date -Format 'yyyy-MM-dd')/daily_tech_trends.md"
```

**Quality Check**:
- [ ] Trends from primary sources (not aggregators)
- [ ] Technical depth present (not just headlines)
- [ ] Systemic significance identified
- [ ] No hype language or price speculation

## ⏰ Recommended Schedule
Run this workflow:
- **Daily at 09:00** (morning scan for overnight developments)
- **Focus**: Quality over quantity (1-3 excellent trends > 10 mediocre)

## 📊 Expected Output

### daily_tech_trends.md
```markdown
# Daily Tech Trends Report: 2026-02-08

**Project**: lookforward (High-Signal Mode)

---

## Trend 1: DeepSeek R1 Architecture Analysis

**Source**: ArXiv Research Paper (https://arxiv.org/...)
**Source Type**: Primary (Research Paper)
**Technical Significance**: High

**Why it Matters**:
เปลี่ยนโครงสร้างต้นทุน AI training ของโลก

**Key Facts**:
- Training cost: $5.6M (vs GPT-4: $100M+)
- Open-source architecture
- Competitive with GPT-4 on benchmarks
- MoE (Mixture of Experts) efficiency

**Potential Insight Score**: 4-5 (Systemic impact on AI democratization)

---

## Trend 2: [Another High-Signal Trend]

...
```

## 🚨 Troubleshooting

### No high-signal trends found
- **This is acceptable** - Report "No High-Signal Trends Found"
- Quality > Quantity - Don't force content from weak trends
- Try again tomorrow

### AI client not configured
```powershell
# Check .env file
code .env

# Ensure AI_PROVIDER and API keys are set
```

### Trends lack technical depth
- Adjust TrendResearcher prompts to emphasize technical detail
- Focus on primary sources only
- Increase Insight Score threshold

## ✅ Success Criteria
- **Minimum**: 1 high-signal trend from primary source
- **Ideal**: 2-3 trends with systemic significance
- **Quality Gate**: All trends have potential Insight Score ≥ 4
- **Execution time**: < 15 minutes (quality research takes time)

## 📝 Next Steps
After trends are identified:
1. Review `daily_tech_trends.md`
2. Select 1-2 trends with highest systemic impact
3. Run `authority-content-pipeline` workflow with selected trends

## 🎯 Authority Standards

**Remember**:
- We scan for **insights**, not headlines
- We prioritize **systemic significance**, not viral potential
- We value **technical depth**, not clickbait
- We build **authority**, not noise

---

**Version**: 2.0 (Authority Edition)  
**Last Updated**: 2026-02-08  
**Alignment**: lookforward Brand (Tech Authority)
