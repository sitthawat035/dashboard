#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PerformanceAnalyzer - Analyze published content performance (100% FREE)

Usage:
    python analyzer.py --performance 05_Published/2026-02-07/performance_data.json
    python analyzer.py --summary weekly
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import (
    setup_logger, load_json, save_json, save_markdown,
    get_date_str, ensure_dir,
    print_header, print_success, print_error, print_info
)
from shared.config import get_config


class PerformanceAnalyzer:
    """
    Analyze published content performance (100% FREE, math-based).
    """
    
    def __init__(self):
        """Initialize analyzer."""
        self.config = get_config()
        self.logger = setup_logger(
            "PerformanceAnalyzer",
            self.config.paths["error_logs"] / f"{get_date_str()}_PerformanceAnalyzer.log"
        )
    
    def calculate_engagement_rate(self, likes: int, comments: int, shares: int, followers: int) -> float:
        """Calculate engagement rate (%)."""
        if followers == 0:
            return 0.0
        
        total_engagement = likes + (comments * 2) + (shares * 3)  # Weighted
        return (total_engagement / followers) * 100
    
    def calculate_virality_score(self, shares: int, reach: int, impressions: int) -> float:
        """Calculate virality score (0-100)."""
        if impressions == 0:
            return 0.0
        
        # Virality = (shares * reach) / impressions * 100
        virality = (shares * reach) / impressions * 100
        return min(virality, 100)  # Cap at 100
    
    def analyze_post(self, post_data: dict) -> dict:
        """
        Analyze single post performance.
        
        Args:
            post_data: Post metrics dictionary
            
        Returns:
            Analysis results
        """
        metrics = post_data.get("metrics", {})
        
        # Extract metrics
        likes = metrics.get("likes", 0)
        comments = metrics.get("comments", 0)
        shares = metrics.get("shares", 0)
        reach = metrics.get("reach", 0)
        impressions = metrics.get("impressions", 0)
        followers = metrics.get("followers", 1000)  # Default
        
        # Calculate scores
        engagement_rate = self.calculate_engagement_rate(likes, comments, shares, followers)
        virality_score = self.calculate_virality_score(shares, reach, impressions)
        
        # Grade performance
        if engagement_rate >= 5:
            performance_grade = "A (ยอดเยี่ยม)"
        elif engagement_rate >= 3:
            performance_grade = "B (ดีมาก)"
        elif engagement_rate >= 2:
            performance_grade = "C (ดี)"
        elif engagement_rate >= 1:
            performance_grade = "D (พอใช้)"
        else:
            performance_grade = "F (ต่ำ)"
        
        # Insights
        insights = []
        
        if engagement_rate >= 5:
            insights.append("🔥 Engagement สูงมาก - เนื้อหาโดนใจมาก!")
        elif engagement_rate < 1:
            insights.append("⚠️  Engagement ต่ำ - ลองปรับเนื้อหาหรือช่วงเวลาโพสต์")
        
        if virality_score >= 10:
            insights.append("🚀 กำลังไวรัล - มีการแชร์เยอะมาก!")
        
        if shares > (likes / 10):
            insights.append("💡 Content ชวนแชร์สูง - เหมาะทำต่อในธีมนี้")
        
        if comments > (likes / 5):
            insights.append("💬 กระตุ้นคลอมเมนต์ได้ดี - คนสนใจคุยกัน")
        
        return {
            "post_id": post_data.get("post_id", "unknown"),
            "topic": post_data.get("topic", "Unknown"),
            "platform": post_data.get("platform", "Unknown"),
            "engagement_rate": round(engagement_rate, 2),
            "virality_score": round(virality_score, 2),
            "performance_grade": performance_grade,
            "metrics": {
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "reach": reach,
                "impressions": impressions
            },
            "insights": insights
        }
    
    def generate_weekly_report(self, posts: list[dict]) -> dict:
        """
        Generate weekly performance summary.
        
        Args:
            posts: List of post analyses
            
        Returns:
            Weekly summary
        """
        if not posts:
            return {}
        
        # Aggregate metrics
        total_likes = sum(p["metrics"]["likes"] for p in posts)
        total_comments = sum(p["metrics"]["comments"] for p in posts)
        total_shares = sum(p["metrics"]["shares"] for p in posts)
        total_reach = sum(p["metrics"]["reach"] for p in posts)
        
        avg_engagement = sum(p["engagement_rate"] for p in posts) / len(posts)
        avg_virality = sum(p["virality_score"] for p in posts) / len(posts)
        
        # Top performers
        top_engagement = max(posts, key=lambda p: p["engagement_rate"])
        top_viral = max(posts, key=lambda p: p["virality_score"])
        
        # Platform breakdown
        platform_stats = defaultdict(list)
        for post in posts:
            platform_stats[post["platform"]].append(post["engagement_rate"])
        
        platform_avg = {
            platform: sum(rates) / len(rates)
            for platform, rates in platform_stats.items()
        }
        
        return {
            "period": f"{len(posts)} posts analyzed",
            "total_metrics": {
                "likes": total_likes,
                "comments": total_comments,
                "shares": total_shares,
                "reach": total_reach
            },
            "averages": {
                "engagement_rate": round(avg_engagement, 2),
                "virality_score": round(avg_virality, 2)
            },
            "top_performers": {
                "highest_engagement": {
                    "topic": top_engagement["topic"],
                    "rate": top_engagement["engagement_rate"]
                },
                "most_viral": {
                    "topic": top_viral["topic"],
                    "score": top_viral["virality_score"]
                }
            },
            "platform_performance": platform_avg,
            "recommendations": self._generate_recommendations(posts)
        }
    
    def _generate_recommendations(self, posts: list[dict]) -> list[str]:
        """Generate recommendations based on performance."""
        recs = []
        
        avg_engagement = sum(p["engagement_rate"] for p in posts) / len(posts)
        
        if avg_engagement < 2:
            recs.append("📌 Engagement ต่ำโดยรวม - ลองทดสอบเนื้อหาหรือช่วงเวลาใหม่")
        
        # Find best platform
        platform_stats = defaultdict(list)
        for post in posts:
            platform_stats[post["platform"]].append(post["engagement_rate"])
        
        if platform_stats:
            best_platform = max(platform_stats.items(), key=lambda x: sum(x[1])/len(x[1]))
            recs.append(f"🎯 {best_platform[0]} ทำงานได้ดีที่สุด - ควรโฟกัสที่นี่")
        
        # Check sharing
        avg_shares = sum(p["metrics"]["shares"] for p in posts) / len(posts)
        if avg_shares < 5:
            recs.append("💡 การแชร์ต่ำ - ลองเพิ่ม shareable content เช่นข้อมูลน่ารู้")
        
        return recs
    
    def save_report(self, analyses: list[dict], summary: dict, output_dir: Path = None) -> Path:
        """Save performance report."""
        if output_dir is None:
            output_dir = self.config.paths["analytics"] / "reports" / get_date_str()
        
        ensure_dir(output_dir)
        
        # Generate markdown report
        lines = [
            f"# Performance Analysis Report\n",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            "---\n",
            "## 📊 Summary\n",
            f"**Period**: {summary['period']}  ",
            f"**Average Engagement Rate**: {summary['averages']['engagement_rate']}%  ",
            f"**Average Virality Score**: {summary['averages']['virality_score']}\n",
            "## 🏆 Top Performers\n",
            f"**Highest Engagement**: {summary['top_performers']['highest_engagement']['topic']} ({summary['top_performers']['highest_engagement']['rate']}%)  ",
            f"**Most Viral**: {summary['top_performers']['most_viral']['topic']} (score: {summary['top_performers']['most_viral']['score']})\n",
            "## 🎯 Platform Performance\n"
        ]
        
        for platform, avg in summary['platform_performance'].items():
            lines.append(f"- **{platform}**: {avg:.2f}% engagement")
        
        lines.extend([
            "\n## 💡 Recommendations\n"
        ])
        
        for rec in summary['recommendations']:
            lines.append(f"- {rec}")
        
        lines.append("\n---\n## 📝 Individual Post Performance\n")
        
        for analysis in analyses:
            lines.extend([
                f"### {analysis['topic']} ({analysis['platform']})\n",
                f"- **Grade**: {analysis['performance_grade']}",
                f"- **Engagement Rate**: {analysis['engagement_rate']}%",
                f"- **Virality Score**: {analysis['virality_score']}",
                f"- **Metrics**: {analysis['metrics']['likes']} likes, {analysis['metrics']['comments']} comments, {analysis['metrics']['shares']} shares\n"
            ])
            
            if analysis['insights']:
                lines.append("**Insights**:")
                for insight in analysis['insights']:
                    lines.append(f"  - {insight}")
                lines.append("")
        
        # Save report
        report_path = output_dir / "performance_report.md"
        save_markdown("\n".join(lines), report_path)
        
        # Save JSON data
        data_path = output_dir / "performance_data.json"
        save_json({"analyses": analyses, "summary": summary}, data_path)
        
        return report_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze content performance (FREE)")
    parser.add_argument(
        "--performance",
        help="Path to performance data JSON"
    )
    parser.add_argument(
        "--summary",
        choices=["weekly", "monthly"],
        help="Generate summary report"
    )
    
    args = parser.parse_args()
    
    print_header("📊 PERFORMANCE ANALYZER - ZERO COST")
    
    # Create analyzer
    analyzer = PerformanceAnalyzer()
    
    # For demo, create sample data
    sample_posts = [
        {
            "post_id": "1",
            "topic": "Viral Trend #1",
            "platform": "Facebook",
            "metrics": {
                "likes": 1500,
                "comments": 85,
                "shares": 120,
                "reach": 25000,
                "impressions": 35000,
                "followers": 10000
            }
        },
        {
            "post_id": "2",
            "topic": "Trending Topic #2",
            "platform": "Instagram",
            "metrics": {
                "likes": 800,
                "comments": 45,
                "shares": 30,
                "reach": 15000,
                "impressions": 22000,
                "followers": 10000
            }
        }
    ]
    
    print_info("Analyzing posts...")
    
    # Analyze each post
    analyses = [analyzer.analyze_post(post) for post in sample_posts]
    
    for analysis in analyses:
        print_success(f"{analysis['topic']}: {analysis['performance_grade']} ({analysis['engagement_rate']}%)")
    
    # Generate summary
    summary = analyzer.generate_weekly_report(analyses)
    
    # Save report
    report_path = analyzer.save_report(analyses, summary)
    
    print_success(f"\n✅ Report saved: {report_path}")
    print_info(f"\n📈 Avg Engagement: {summary['averages']['engagement_rate']}%")


if __name__ == "__main__":
    main()
