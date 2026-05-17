---
name: PerformanceAnalyzer
description: Analyze published content performance and generate insights for optimization
---

# PerformanceAnalyzer Skill

## 🎯 Purpose
Track and analyze engagement metrics from published content to identify patterns, optimize strategy, and improve future content performance.

## 📥 Input Sources

### 1. Published Content Archive
`06_Published/YYYY-MM-DD_[topic]_[platform].md`

Contains:
- Original post content
- Publishing timestamp
- Platform

### 2. Manual Engagement Data (Initial)
User provides metrics via template:
```json
{
  "post_id": "2026-02-07_viral-topic_facebook",
  "platform": "facebook",
  "published_at": "2026-02-07T18:30:00+07:00",
  "metrics": {
    "likes": 150,
    "comments": 28,
    "shares": 12,
    "reach": 5000,
    "impressions": 7500,
    "clicks": 45
  },
  "demographics": {
    "age_range": "18-34",
    "top_location": "Bangkok"
  }
}
```

### 3. Future: API Integration (Optional)
- Facebook Graph API
- Instagram API
- TikTok Analytics API

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

#### Virality Score
```python
virality_score = (shares * 3) + (comments * 2) + (likes * 1)
```

#### ROI (Time Investment)
```python
roi = engagement_rate / time_invested
# Higher = better return on time spent
```

### Step 3: Pattern Recognition

Analyze by:
- **Content Type**: Meme, educational, news, etc.
- **Hook Style**: Question, FOMO, story, etc.
- **Topic Category**: Trending, evergreen, niche
- **Platform**: Facebook, TikTok, Instagram
- **Posting Time**: Hour of day, day of week
- **Media Type**: Image, video, carousel

### Step 4: Generate Insights

## 📄 Output Formats

### Daily Performance Report
Save to: `07_Analytics/performance_metrics/YYYY-MM-DD_daily.md`

```markdown
# Daily Performance Report - 2026-02-07

## 📊 Summary
- **Posts Published**: 3
- **Total Engagement**: 245 (likes + comments + shares)
- **Avg Engagement Rate**: 4.2%
- **Best Performer**: "Viral Topic A" (8.5% engagement)
- **Worst Performer**: "Topic C" (1.8% engagement)

---

## 📈 Individual Post Performance

### Post 1: [Viral Topic A] - Facebook
- **Published**: 18:30
- **Likes**: 150 | **Comments**: 28 | **Shares**: 12
- **Reach**: 5,000 | **Engagement Rate**: 8.5% ⬆️ 
- **Virality Score**: 242 🔥

**Why it worked**:
- Posted during peak time (18:30)
- Strong hook with question format
- High-quality media (vibrant image)
- Topic was still trending (< 24h old)

**Content elements**:
- Hook: "รู้มั้ยว่าทำไม..."
- Media: Single bright image
- CTA: Multiple options (like, comment, share)
- Hashtags: 4 trending + 1 niche

---

### Post 2: [Topic B] - TikTok
- **Views**: 2,500 | **Likes**: 85 | **Comments**: 12 | **Shares**: 8
- **Engagement Rate**: 4.2%
- **Virality Score**: 121

**Moderate performance**:
- Good engagement for TikTok
- Could improve: Hook could be punchier

---

### Post 3: [Topic C] - Facebook
- **Reach**: 1,200 | **Engagement Rate**: 1.8% ⬇️

**Why it underperformed**:
- Posted too late (trend already fading)
- Generic hook, low curiosity
- Weak CTA
- Media quality lower than Posts 1-2

**Improvement needed**: Better timing, stronger hook

---

## 🎯 Key Takeaways

### What Worked ✅
1. Posting during peak hours (18:00-20:00)
2. Question-based hooks perform best
3. Trending topics < 24h old get 2x engagement
4. Multiple CTA options increase engagement

### What Didn't Work ❌
1. Late posting on fading trends
2. Generic hooks without curiosity gap
3. Lower quality media correlated with lower engagement

---

## 💡 Recommendations for Tomorrow
- Focus on trends < 24h old
- Use question-based hooks (proven winner)
- Post between 18:00-20:00
- Ensure all media is high-quality
- Test video content on TikTok (higher potential reach)
```

---

### Weekly Summary Report
Save to: `07_Analytics/performance_metrics/YYYY-WW_weekly.md`

```markdown
# Weekly Performance Report - Week 6, 2026

## 📊 Overview
- **Posts Published**: 15
- **Total Reach**: 45,000
- **Total Engagement**: 1,850
- **Avg Engagement Rate**: 4.1%
- **New Followers**: 127 🎉

---

## 🏆 Top 5 Performers

| Rank | Post | Platform | Eng Rate | Virality Score |
|------|------|----------|----------|----------------|
| 1 | [Topic A] | Facebook | 8.5% | 242 |
| 2 | [Topic D] | TikTok | 7.2% | 198 |
| 3 | [Topic F] | Instagram | 6.8% | 175 |
| 4 | [Topic B] | Facebook | 5.5% | 156 |
| 5 | [Topic X] | TikTok | 5.1% | 142 |

**Common elements**:
- All used question hooks
- All posted during peak hours
- All had trending hashtags < 48h old
- 4/5 used high-quality images

→ Copy to: `07_Analytics/top_performers/week-06.md`

---

## 📉 Bottom 3 Performers

Analyze failures to avoid repeating:
1. [Topic C] - 1.8% (late to trend)
2. [Topic M] - 2.1% (weak hook)
3. [Topic R] - 2.3% (poor media quality)

---

## 📈 Performance by Category

### By Content Type
| Type | Avg Eng Rate | Posts |
|------|--------------|-------|
| Meme/Humor | 6.2% | 5 |
| Educational | 4.5% | 4 |
| News/Trending | 5.8% | 4 |
| Debate | 3.2% | 2 |

**Insight**: Humor performs best, debates underperform

### By Platform
| Platform | Avg Eng Rate | Posts |
|----------|--------------|-------|
| TikTok | 5.5% | 6 |
| Facebook | 4.0% | 7 |
| Instagram | 3.5% | 2 |

**Insight**: TikTok has highest engagement, expand presence there

### By Posting Time
| Time Slot | Avg Eng Rate | Posts |
|-----------|--------------|-------|
| 18:00-20:00 | 6.8% | 8 |
| 12:00-14:00 | 3.5% | 4 |
| Other | 2.2% | 3 |

**Insight**: Evening posts dominate, schedule more at 18:00-20:00

---

## 💡 Strategic Recommendations

### Double Down On
1. **Question hooks** - Consistently highest engagement
2. **TikTok platform** - Best engagement rate
3. **Evening posts** - 18:00-20:00 sweet spot
4. **Humor content** - Outperforms educational

### Test & Experiment
1. Video content on Facebook (only tested 2 so far)
2. Carousel posts on Instagram
3. Controversial/debate topics (carefully)
4. Morning posts (09:00-11:00) - underexplored

### Stop/Reduce
1. Posting outside peak hours (< 3% engagement)
2. Late-to-trend content (> 48h old trends)
3. Generic hooks without curiosity

---

## 🎯 Goals for Next Week
- Publish 18 posts (↑ 20% volume)
- Target 5% avg engagement rate (↑ from 4.1%)
- Gain 150+ followers (↑ from 127)
- Test 3 video posts on Facebook
- Focus 60% content on TikTok

```

---

### Lessons Learned Log
Save to: `07_Analytics/lessons_learned/YYYY-MM.md`

```markdown
# Lessons Learned - February 2026

## 🎓 Key Discoveries

### 1. Question Hooks Dominate
**Finding**: Posts starting with "รู้มั้ยว่า..." averaged 6.5% engagement vs 3.2% for other hooks.

**Evidence**:
- 12 posts tested with question hooks
- Average engagement: 6.5%
- Control group (other hooks): 3.2%
- Statistical significance: High

**Action**: Update ContentWriter skill to prioritize question-based hooks

**Updated**: 2026-02-15

---

### 2. Trend Lifespan Critical
**Finding**: Trending topics lose 50% engagement potential after 36 hours.

**Evidence**:
- Posts on trends < 24h: 6.8% avg engagement
- Posts on trends 24-48h: 4.2% avg engagement  
- Posts on trends > 48h: 2.1% avg engagement

**Action**: 
- Update TrendResearcher to flag trend age
- ContentStrategist to prioritize < 24h trends
- Automate daily scans

**Updated**: 2026-02-18

---

### 3. TikTok = Best ROI
**Finding**: TikTok content gets 40% higher engagement with 30% less effort.

**Evidence**:
- TikTok avg engagement: 5.5%
- Facebook avg engagement: 4.0%
- TikTok posts are shorter (less writing time)

**Action**: Shift content mix to 50% TikTok, 30% Facebook, 20% Instagram

**Updated**: 2026-02-22

---

## 🚫 What NOT to Do

### Don't Chase Every Trend
**Mistake**: Posting on 10 different trends in one day

**Result**: Content quality suffered, engagement dropped to 2.5%

**Lesson**: Focus on 2-3 quality trends per day, not 10 mediocre ones

---

### Don't Ignore Media Quality
**Mistake**: Using low-res images for "quick" posts

**Result**: 60% lower engagement compared to high-quality media posts

**Lesson**: Never compromise on media quality, it's worth the extra time

---

## 📚 Best Practices Codified

1. ✅ Post trending content within 24h of trend emergence
2. ✅ Use question hooks for 70% of posts
3. ✅ Schedule posts for 18:00-20:00 time slot
4. ✅ Always use high-quality media (min 1920px)
5. ✅ Include 3+ engagement CTAs per post
6. ✅ Test variations (A/B) for high-potential topics
7. ✅ Review analytics weekly, adjust monthly
8. ✅ Focus on TikTok for best ROI
```

---

## 🔄 Workflow Integration

### After Publishing
```python
# Wait 48 hours for metrics to stabilize
time.sleep(48 * 3600)

# Collect metrics (manual or API)
metrics = collect_metrics(post_id)

# Run analysis
agent invoke PerformanceAnalyzer --post-id {post_id}

# Store in analytics folder
save_analysis("07_Analytics/performance_metrics/")
```

### Weekly Review
```python
# Every Monday morning
agent invoke PerformanceAnalyzer --period weekly --week {week_number}

# Review report
code "07_Analytics/performance_metrics/{year}-W{week}_weekly.md"

# Update strategy based on insights
```

## 📊 Visualization (Optional Future Enhancement)

Generate charts:
- Engagement rate over time (line chart)
- Performance by platform (bar chart)
- Top performing content types (pie chart)
- Posting time heatmap

Tools: Python (matplotlib/plotly), Excel, Google Data Studio

## 💡 Usage Example

```bash
# Analyze single post
agent invoke PerformanceAnalyzer --post 06_Published/2026-02-07_viral-topic_facebook.md

# Weekly analysis
agent invoke PerformanceAnalyzer --weekly --week 6

# Monthly analysis
agent invoke PerformanceAnalyzer --monthly --month 2
```

## ✅ Success Criteria
- Insights are actionable and specific
- Patterns identified lead to measurable improvement
- Weekly engagement rate increases month-over-month
- Lessons learned are codified in brand guidelines
- Data-driven decisions replace guesswork
