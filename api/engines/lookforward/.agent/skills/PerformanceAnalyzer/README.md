# PerformanceAnalyzer Usage Guide

**Purpose**: Track and analyze engagement metrics from published content to identify patterns, optimize strategy, and improve future content performance for **"lookforward"** authority content.

---

## 🎯 Core Mission

Analyze performance to:
- **Identify patterns** - What works for authority content?
- **Optimize strategy** - Data-driven decisions
- **Improve quality** - Learn from successes and failures
- **Compound authority** - Build on what resonates

---

## 📊 Analysis Process

### Step 1: Data Collection
Gather metrics for time period (daily/weekly/monthly):
```python
# Load all published posts from date range
posts = load_published_posts(start_date, end_date)

# For each post, load metrics
for post in posts:
    metrics = load_metrics(post.id)
    post.attach_metrics(metrics)
```

### Step 2: Calculate KPIs

#### Engagement Rate
```python
engagement_rate = (likes + comments + shares) / reach * 100
```

#### Authority Score (Custom for lookforward)
```python
# Weighted scoring for authority content
authority_score = (
    (comments * 5) +      # Deep engagement
    (shares * 3) +        # Endorsement
    (saves * 4) +         # Value retention
    (likes * 1)           # Basic engagement
) / reach * 100
```

#### Insight Resonance
```python
# Correlation between Insight Score and engagement
insight_resonance = engagement_rate / insight_score
# Higher = insights are resonating with audience
```

### Step 3: Pattern Recognition

Analyze by:
- **Insight Score** (1-5) vs Engagement
- **Content Depth** (word count, technical detail)
- **Topic Category** (AI, Crypto, Tech)
- **Hook Style** (Contrarian, System Logic, Calm Disrupt)
- **Posting Time** (hour of day, day of week)
- **Media Type** (diagram, screenshot, chart)

### Step 4: Generate Insights

---

## 🚀 Quick Start

### 1. Analyze Performance
```powershell
# Analyze single post
python .agent/skills/PerformanceAnalyzer/analyzer.py --post 05_Published/2026-02-08_deepseek_architecture_facebook.md

# Daily analysis
python .agent/skills/PerformanceAnalyzer/analyzer.py --daily --date 2026-02-08

# Weekly analysis
python .agent/skills/PerformanceAnalyzer/analyzer.py --weekly --week 6

# Monthly analysis
python .agent/skills/PerformanceAnalyzer/analyzer.py --monthly --month 2
```

---

## 📄 Output Formats

### Daily Performance Report
Save to: `07_Analytics/performance_metrics/YYYY-MM-DD_daily.md`

```markdown
# Daily Performance Report - 2026-02-08

## 📊 Summary
- **Posts Published**: 2
- **Total Engagement**: 185 (weighted authority score)
- **Avg Engagement Rate**: 6.2%
- **Avg Insight Score**: 4.5/5
- **Best Performer**: "DeepSeek Architecture" (8.5% engagement)

---

## 📈 Individual Post Performance

### Post 1: DeepSeek R1 Architecture - Facebook
- **Published**: 14:30
- **Likes**: 120 | **Comments**: 35 | **Shares**: 18 | **Saves**: 12
- **Reach**: 4,200 | **Engagement Rate**: 8.5% ⬆️
- **Authority Score**: 245 🔥
- **Insight Score**: 4/5

**Why it worked**:
- Strong non-obvious angle: "architecture > budget"
- Technical depth with accessible explanation
- Systemic connection to AI democratization
- Calm, professional tone (no hype)
- Posted during optimal time (14:30)

**Content elements**:
- Hook: Contrarian ("ไม่ได้แค่ถูกกว่า")
- Structure: Update → Breakdown → Impact → Vision
- Media: Architecture diagram (technical)
- CTA: Thought-provoking question

---

## 🎯 Key Takeaways

### What Worked ✅
1. **High Insight Score (4-5)** correlates with 2x engagement
2. **Systemic analysis** drives more comments (deep engagement)
3. **Technical diagrams** outperform generic stock photos
4. **Calm tone** builds trust, doesn't sacrifice engagement

### What Didn't Work ❌
1. Posts with Insight Score < 3 underperformed (< 3% engagement)
2. Generic hooks without non-obvious angle got ignored

---

## 💡 Recommendations for Tomorrow
- Continue focus on Insight Score 4-5 content
- Use technical diagrams/charts for all posts
- Test contrarian hooks (proven winner today)
- Maintain calm, professional tone
```

---

### Weekly Summary Report
Save to: `07_Analytics/performance_metrics/YYYY-WW_weekly.md`

```markdown
# Weekly Performance Report - Week 6, 2026

## 📊 Overview
- **Posts Published**: 12
- **Total Reach**: 38,000
- **Total Engagement**: 1,650
- **Avg Engagement Rate**: 5.8%
- **Avg Insight Score**: 4.2/5
- **New Followers**: 89 🎉

---

## 🏆 Top 5 Performers

| Rank | Post | Insight | Eng Rate | Authority Score |
|------|------|---------|----------|-----------------|
| 1 | DeepSeek Architecture | 4/5 | 8.5% | 245 |
| 2 | Crypto Regulation Analysis | 5/5 | 7.8% | 218 |
| 3 | AI Training Cost Breakdown | 4/5 | 6.9% | 195 |
| 4 | Tech Monopoly Systems | 5/5 | 6.5% | 187 |
| 5 | Open Source Impact | 4/5 | 6.2% | 172 |

**Common elements**:
- All had Insight Score ≥ 4/5
- All used systemic analysis approach
- All had technical visuals (diagrams/charts)
- All maintained calm, professional tone
- 4/5 used contrarian or system logic hooks

→ Copy to: `07_Analytics/top_performers/week-06.md`

---

## 📈 Performance by Category

### By Insight Score
| Insight Score | Avg Eng Rate | Posts | Pattern |
|---------------|--------------|-------|---------|
| 5/5 (Excellent) | 7.2% | 3 | Exceptional resonance |
| 4/5 (Good) | 6.1% | 6 | Strong performance |
| 3/5 (Fair) | 2.8% | 2 | Below threshold |
| 2/5 (Weak) | 1.5% | 1 | Rejected by audience |

**Critical Insight**: Insight Score 4+ is mandatory for success

### By Hook Style
| Hook Type | Avg Eng Rate | Posts |
|-----------|--------------|-------|
| Contrarian | 7.1% | 4 |
| System Logic | 6.5% | 5 |
| Calm Disrupt | 5.8% | 3 |

**Insight**: All authority-aligned hooks perform well

### By Media Type
| Media Type | Avg Eng Rate | Posts |
|------------|--------------|-------|
| Technical Diagram | 6.8% | 5 |
| Data Chart | 6.2% | 4 |
| Screenshot | 5.5% | 3 |

**Insight**: Technical visuals significantly outperform generic images

---

## 💡 Strategic Recommendations

### Double Down On
1. **Insight Score 4-5 content** - Non-negotiable quality bar
2. **Systemic analysis** - Audience craves depth
3. **Technical visuals** - Diagrams, charts, screenshots
4. **Contrarian hooks** - Highest engagement driver
5. **Calm professional tone** - Builds authority without sacrificing engagement

### Test & Experiment
1. Longer-form analysis (1500+ words)
2. Multi-part series on complex topics
3. Interactive elements (polls on technical questions)
4. Video explanations of diagrams

### Stop/Reduce
1. Content with Insight Score < 4 (doesn't meet brand standard)
2. Generic stock photos (use technical visuals only)
3. News summarization without analysis

---

## 🎯 Goals for Next Week
- Publish 12 posts (maintain quality over quantity)
- Target 6.5% avg engagement rate (↑ from 5.8%)
- Maintain Insight Score avg ≥ 4.0
- Gain 100+ followers (↑ from 89)
- Test 2 video content pieces
```

---

### Lessons Learned Log
Save to: `07_Analytics/lessons_learned/YYYY-MM.md`

```markdown
# Lessons Learned - February 2026

## 🎓 Key Discoveries

### 1. Insight Score is the Primary Driver
**Finding**: Posts with Insight Score 4-5 get 3x engagement vs Score 2-3

**Evidence**:
- Insight Score 5: 7.2% avg engagement
- Insight Score 4: 6.1% avg engagement
- Insight Score 3: 2.8% avg engagement
- Insight Score 2: 1.5% avg engagement

**Action**: Enforce minimum Insight Score 4 for all published content

**Updated**: 2026-02-08

---

### 2. Authority Doesn't Sacrifice Engagement
**Finding**: Calm, professional tone performs as well as "viral" tactics

**Evidence**:
- Authority content (calm tone): 5.8% avg engagement
- Industry benchmark (viral tactics): 4-5% avg engagement
- Our content builds trust AND engagement

**Action**: Continue authority-first approach, it's working

**Updated**: 2026-02-08

---

### 3. Technical Visuals Drive Credibility
**Finding**: Technical diagrams/charts get 40% higher engagement than stock photos

**Evidence**:
- Technical diagrams: 6.8% avg engagement
- Data charts: 6.2% avg engagement
- Stock photos: 4.1% avg engagement (when tested)

**Action**: Update MediaSourcing to prioritize technical visuals only

**Updated**: 2026-02-08

---

## 📚 Best Practices Codified

1. ✅ Publish only Insight Score 4-5 content
2. ✅ Use systemic analysis approach (Update → Breakdown → Impact → Vision)
3. ✅ Include technical visuals (diagrams, charts, screenshots)
4. ✅ Maintain calm, professional tone (no hype)
5. ✅ Use contrarian or system logic hooks
6. ✅ Focus on depth over speed
7. ✅ Quality > Quantity (12 great posts > 20 mediocre)
```

---

## 📥 Input Sources

### 1. Published Content Archive
`05_Published/YYYY-MM-DD_[topic]_[platform].md`

Contains:
- Original post content
- Publishing timestamp
- Platform
- Insight Score

### 2. Manual Engagement Data (Initial)
User provides metrics via template:
```json
{
  "post_id": "2026-02-08_deepseek_architecture_facebook",
  "platform": "facebook",
  "published_at": "2026-02-08T14:30:00+07:00",
  "insight_score": 4,
  "metrics": {
    "likes": 120,
    "comments": 35,
    "shares": 18,
    "saves": 12,
    "reach": 4200,
    "impressions": 6800
  }
}
```

### 3. Future: API Integration (Optional)
- Facebook Graph API
- Instagram API
- Twitter/X API

---

## 🔄 Workflow Integration

### After Publishing (48 hours)
```powershell
# Collect metrics (manual or API)
# Run analysis
python .agent/skills/PerformanceAnalyzer/analyzer.py --post 05_Published/2026-02-08_deepseek_architecture_facebook.md

# Store in analytics folder
# Review insights
```

### Weekly Review (Every Monday)
```powershell
# Generate weekly report
python .agent/skills/PerformanceAnalyzer/analyzer.py --weekly --week 6

# Review report
code 07_Analytics/performance_metrics/2026-W06_weekly.md

# Update strategy based on insights
```

---

## ✅ Success Criteria

- Insights are actionable and specific
- Patterns identified lead to measurable improvement
- Weekly engagement rate increases month-over-month
- Lessons learned are codified in brand guidelines
- Data-driven decisions replace guesswork
- Authority compounds over time

---

**Version**: 2.0 (Authority Edition)  
**Last Updated**: 2026-02-08  
**Alignment**: lookforward Brand (Tech Authority)
