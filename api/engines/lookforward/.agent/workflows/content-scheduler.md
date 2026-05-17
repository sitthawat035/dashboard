---
description: Schedule approved content for optimal posting times
---

# Content Scheduler Workflow (lookforward Edition)

Organize and schedule approved authority content from `05_Published/` to publishing queue.

## 🎯 Objective
Optimize posting schedule for authority content based on:
- Audience engagement patterns (data-driven)
- Content depth (longer analysis needs optimal timing)
- Insight Score distribution (balance Score 4 and 5 posts)
- Authority building momentum

**Philosophy**: "Quality timing > Quantity posting" - Strategic scheduling for maximum impact.

## 📋 Steps

### 1. Review Published Content Queue

```powershell
# List all approved authority content
Get-ChildItem "05_Published/" | Format-Table Name, LastWriteTime
```

**Quality Check**:
- [ ] All content has Insight Score ≥ 4
- [ ] Fact accuracy verified
- [ ] Technical visuals linked
- [ ] No hype language present

### 2. Check Calendar

Review existing schedule:
```powershell
code "08_Calendar/weekly_schedule.json"
```

### 3. Optimal Time Slots (Data-Driven - Update Based on Performance)

**Initial Baseline** (to be optimized via performance-review):

| Platform | Best Times (Thailand) | Peak Days | Authority Content Focus |
|----------|----------------------|-----------|------------------------|
| **Facebook** | 14:00-15:00, 19:00-21:00 | Mon-Thu | Primary (long-form analysis) |
| **Twitter/X** | 12:00-13:00, 17:00-18:00 | Mon-Fri | Secondary (thread summaries) |
| **LinkedIn** | 08:00-09:00, 17:00-18:00 | Tue-Thu | Future (professional audience) |

**Note**: Update these times based on weekly performance reviews.

### 4. Scheduling Logic (Authority-Focused)

#### Priority Levels
1. **🔥 High-Impact** (Insight Score 5): Schedule for peak engagement times
2. **⚡ Strong** (Insight Score 4): Schedule for secondary peak times
3. **📌 Evergreen**: Deep analysis with long shelf-life, flexible timing

#### Platform Distribution (Authority Content)
- **80% Facebook** (primary platform, supports long-form)
- **20% Twitter/X** (thread format for summaries)
- **Future: LinkedIn** (professional tech audience)

#### Daily Posting Frequency (Quality > Quantity)
- **Minimum**: 1 post/day (maintain consistency)
- **Optimal**: 1-2 posts/day (avoid overwhelming audience)
- **Maximum**: 2 posts/day (authority content needs digestion time)

**Remember**: 12 excellent posts/week > 20 mediocre ones

### 5. Create Weekly Schedule

// turbo
Generate schedule file:

**File**: `08_Calendar/weekly_schedule.json`

```json
{
  "week": 6,
  "year": 2026,
  "start_date": "2026-02-09",
  "end_date": "2026-02-15",
  "schedule": [
    {
      "date": "2026-02-09",
      "day": "Monday",
      "posts": [
        {
          "time": "14:30",
          "platform": "Facebook",
          "file": "05_Published/2026-02-08_deepseek_architecture_facebook.md",
          "insight_score": 5,
          "priority": "high-impact",
          "estimated_eng_rate": "7-9%",
          "content_type": "Deep Technical Analysis"
        },
        {
          "time": "19:00",
          "platform": "Facebook",
          "file": "05_Published/2026-02-08_crypto_regulation_facebook.md",
          "insight_score": 4,
          "priority": "strong",
          "estimated_eng_rate": "6-8%",
          "content_type": "Systemic Analysis"
        }
      ]
    },
    {
      "date": "2026-02-10",
      "day": "Tuesday",
      "posts": [
        {
          "time": "14:00",
          "platform": "Facebook",
          "file": "05_Published/2026-02-09_ai_training_cost_facebook.md",
          "insight_score": 4,
          "priority": "strong",
          "estimated_eng_rate": "6-7%",
          "content_type": "Data-Driven Analysis"
        }
      ]
    }
  ],
  "summary": {
    "total_posts_scheduled": 12,
    "by_platform": {
      "facebook": 10,
      "twitter": 2
    },
    "by_insight_score": {
      "score_5": 4,
      "score_4": 8
    },
    "avg_insight_score": 4.3,
    "quality_compliance": "100%"
  }
}
```

### 6. Scheduling Best Practices (Authority Content)

#### DO ✅
- **Schedule Insight Score 5 posts for peak times** (maximize impact)
- **Space posts 24 hours apart** (give audience time to digest)
- **Balance Insight Score 4 and 5 throughout week** (maintain quality)
- **Leave buffer for breaking tech news** (high-signal only)
- **Review engagement data weekly** (optimize timing)

#### DON'T ❌
- **Don't post > 2 times/day** (authority content needs time)
- **Don't schedule back-to-back deep dives** (audience fatigue)
- **Don't compromise on Insight Score for frequency** (quality > quantity)
- **Don't ignore performance data** (optimize based on evidence)
- **Don't post during low-engagement windows** (waste of quality content)

### 7. Schedule Posts

#### Option A: Manual Scheduling (Facebook Creator Studio)
```powershell
# Open Facebook Creator Studio
Start-Process "https://business.facebook.com/creatorstudio"

# For each post in schedule:
# 1. Copy post content
# 2. Upload technical visual
# 3. Set publish time (peak engagement window)
# 4. Add first comment with sources/references
# 5. Schedule
```

#### Option B: Automated (Using FacebookPoster Skill)
```powershell
# Use FacebookPoster skill with scheduling
python .agent/skills/FacebookPoster/poster.py --schedule "08_Calendar/weekly_schedule.json"
```

### 8. Post-Publishing Tracking

After post goes live:
```powershell
# Add to published archive with metadata
# File: 05_Published/2026-02-08_deepseek_architecture_facebook.md

# Add frontmatter:
---
published_at: 2026-02-08T14:30:00+07:00
platform: facebook
insight_score: 5
estimated_engagement: 7-9%
actual_engagement: [to be updated after 48h]
---
```

## 📊 Schedule Optimization (Data-Driven)

### Weekly Review Integration
Every Monday (during performance-review):
```bash
# Analyze last week's posting times vs engagement
# Identify best performing time slots
# Update optimal time slots in this workflow
# Adjust this week's schedule accordingly
```

### Insight Score Distribution
**Target Weekly Mix**:
- 30-40% Insight Score 5 posts (high-impact)
- 60-70% Insight Score 4 posts (strong authority)
- 0% Insight Score < 4 (rejected)

**Scheduling Strategy**:
- Insight Score 5 → Peak times (14:00-15:00, 19:00-21:00)
- Insight Score 4 → Secondary peaks (12:00-13:00, 17:00-18:00)

### Content Depth Consideration
- **Deep Dives (1500+ words)**: Schedule for evening (19:00-21:00) when audience has time
- **Standard Analysis (800-1200 words)**: Afternoon (14:00-15:00)
- **Quick Insights (500-800 words)**: Lunchtime (12:00-13:00)

## 🎯 Authority Building Schedule

### Weekly Pattern (Example)
```
Monday:    1 post (Insight Score 5) - Start week strong
Tuesday:   1 post (Insight Score 4) - Maintain momentum
Wednesday: 2 posts (Score 5 + Score 4) - Mid-week peak
Thursday:  1 post (Insight Score 4) - Consistency
Friday:    1 post (Insight Score 5) - End week strong
Saturday:  1 post (Insight Score 4) - Weekend presence
Sunday:    0-1 posts - Rest or evergreen content
```

**Total**: 8-12 posts/week (quality-focused)

## 💡 Usage Example

```bash
# In Engagement directory
cd c:\Users\User\.gemini\antigravity\scratch\content-automation\Engagement

# Generate weekly schedule
agent run content-scheduler --week 6

# Review schedule
code 08_Calendar/weekly_schedule.json

# Verify quality compliance
# - All posts Insight Score ≥ 4? ✅
# - Optimal time distribution? ✅
# - Platform mix correct? ✅

# Proceed with scheduling
```

## ✅ Success Criteria
- Schedule created for full week ahead
- 100% of posts have Insight Score ≥ 4
- Insight Score 5 posts scheduled for peak times
- Posts spaced appropriately (24h+ apart)
- Platform mix matches strategy (80% Facebook)
- Weekly target: 8-12 quality posts

## 🚨 Breaking Tech News Override

For high-signal breaking news:
```bash
# Evaluate Insight Score potential (must be ≥ 4)
# If Score 5 potential:
#   - Bump next scheduled post
#   - Insert at next peak time
# If Score 4:
#   - Add to next available secondary peak
# If Score < 4:
#   - Skip (maintain quality standards)
```

## 📈 Performance-Based Optimization

### Monthly Schedule Review
```markdown
# Update optimal times based on data:

## February 2026 Findings
- Best engagement: 14:30-15:30 (not 14:00-15:00)
- Insight Score 5 posts: 18% higher engagement at 19:00 vs 14:00
- Monday posts: 12% higher engagement than Friday
- Deep dives (1500+ words): Best at 20:00 (not 19:00)

## March 2026 Adjustments
- Shift primary peak to 14:30-15:30
- Schedule all Insight Score 5 at 19:00
- Prioritize Monday/Tuesday for high-impact content
- Move deep dives to 20:00
```

---

**Version**: 2.0 (Authority Edition)  
**Last Updated**: 2026-02-08  
**Alignment**: lookforward Brand (Tech Authority)

**Note**: This workflow evolves based on performance data. Update optimal times monthly based on actual engagement patterns.
