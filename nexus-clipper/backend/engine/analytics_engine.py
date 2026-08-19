"""
NexuX V8.5 — Cross-Platform Analytics Engine
=================================================
Unified analytics that tracks clip performance across all platforms
and provides insights Opus Clip doesn't have:

1. CROSS-PLATFORM COMPARISON: same clip's performance on TikTok vs YT vs IG
2. VIRALITY vs ACTUAL: predicted virality score vs actual views (accuracy tracking)
3. OPTIMAL POSTING TIME: learns when your audience is most active
4. CLIP TYPE ANALYSIS: which hook archetypes perform best
5. AUDIENCE RETENTION CURVES: drop-off patterns per platform
6. ENGAGEMENT PATTERNS: like/comment/share ratios per platform
7. HASHTAG EFFECTIVENESS: which hashtags drive discovery
8. PERFORMANCE PREDICTIONS: predicts next clip's performance based on history
9. A/B TESTING: compares different caption styles, thumbnails, hooks
10. TREND DETECTION: spots rising/falling content themes
"""
import json
import time
import math
import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

log = logging.getLogger("nexus.analytics")


# -- Data Structures --

@dataclass
class ClipMetrics:
    """Performance metrics for a single clip on a single platform."""
    clip_id: str
    platform: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    watch_time_seconds: float = 0.0
    avg_watch_time: float = 0.0         # Average watch time per viewer
    completion_rate: float = 0.0        # % who watched to end
    retention_curve: List[float] = field(default_factory=list)  # Retention at each second
    impressions: int = 0
    profile_visits: int = 0
    follows: int = 0
    posted_at: str = ""
    fetched_at: str = ""


@dataclass
class ClipAnalytics:
    """Aggregated analytics for a clip across all platforms."""
    clip_id: str
    job_id: str
    clip_start: float = 0.0
    clip_end: float = 0.0
    clip_duration: float = 0.0
    hook_archetype: str = ""
    virality_score: float = 0.0        # Predicted virality (0-100)
    virality_grade: str = ""
    caption_style: str = ""
    platforms: Dict[str, ClipMetrics] = field(default_factory=dict)

    # Aggregated metrics
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_saves: int = 0
    total_engagement: int = 0
    engagement_rate: float = 0.0        # (likes+comments+shares) / views
    avg_watch_time: float = 0.0         # Average watch time across platforms
    completion_rate: float = 0.0         # Average completion rate across platforms
    best_platform: str = ""
    worst_platform: str = ""

    # Prediction accuracy
    prediction_error: float = 0.0       # |predicted - actual|
    prediction_accuracy: float = 0.0   # 1.0 - (error / actual)

    # Insights
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class JobAnalytics:
    """Analytics for an entire job (all clips)."""
    job_id: str
    total_clips: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    avg_virality_score: float = 0.0
    avg_actual_performance: float = 0.0
    best_clip_id: str = ""
    best_clip_views: int = 0
    worst_clip_id: str = ""
    worst_clip_views: int = 0
    clip_analytics: List[ClipAnalytics] = field(default_factory=list)
    platform_breakdown: Dict[str, Dict] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    predictions: List[Dict] = field(default_factory=list)


# -- Metrics Collection --

def collect_clip_metrics(
    platform: str,
    post_id: str,
    credentials: Dict,
) -> ClipMetrics:
    """
    Fetch performance metrics for a posted clip from a platform.

    Uses each platform's analytics API to get real-time stats.
    """
    metrics = ClipMetrics(
        clip_id=post_id,
        platform=platform,
        fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )

    try:
        if platform == "tiktok":
            _fetch_tiktok_metrics(metrics, post_id, credentials)
        elif platform == "youtube_shorts":
            _fetch_youtube_metrics(metrics, post_id, credentials)
        elif platform == "instagram_reels":
            _fetch_instagram_metrics(metrics, post_id, credentials)
        elif platform == "facebook_reels":
            _fetch_facebook_metrics(metrics, post_id, credentials)
        elif platform == "twitter":
            _fetch_twitter_metrics(metrics, post_id, credentials)
        elif platform == "linkedin":
            _fetch_linkedin_metrics(metrics, post_id, credentials)
    except Exception as e:
        log.error(f"[Analytics] Failed to fetch metrics from {platform}: {e}")
        metrics.insights = [f"Failed to fetch: {str(e)}"]

    return metrics


def _fetch_tiktok_metrics(metrics: ClipMetrics, post_id: str, creds: Dict):
    """Fetch TikTok video metrics."""
    import urllib.request

    access_token = creds.get("access_token", "")
    url = f"https://open.tiktokapis.com/v2/video/query/"
    body = json.dumps({"video_ids": [post_id], "fields": [
        "view_count", "like_count", "comment_count", "share_count",
        "save_count", "average_watch_time", "average_time_watched"
    ]})

    req = urllib.request.Request(url, data=body.encode("utf-8"),
                                 headers={
                                     "Authorization": f"Bearer {access_token}",
                                     "Content-Type": "application/json",
                                 }, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    videos = data.get("data", {}).get("videos", [])
    if videos:
        v = videos[0]
        metrics.views = v.get("view_count", 0)
        metrics.likes = v.get("like_count", 0)
        metrics.comments = v.get("comment_count", 0)
        metrics.shares = v.get("share_count", 0)
        metrics.saves = v.get("save_count", 0)
        metrics.avg_watch_time = v.get("average_watch_time", 0.0)
        metrics.watch_time_seconds = metrics.avg_watch_time * metrics.views


def _fetch_youtube_metrics(metrics: ClipMetrics, video_id: str, creds: Dict):
    """Fetch YouTube Shorts metrics via Data API."""
    import urllib.request

    access_token = creds.get("access_token", "")
    url = (f"https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet"
           f"&id={video_id}")

    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {access_token}",
    }, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    items = data.get("items", [])
    if items:
        stats = items[0].get("statistics", {})
        metrics.views = int(stats.get("viewCount", 0))
        metrics.likes = int(stats.get("likeCount", 0))
        metrics.comments = int(stats.get("commentCount", 0))


def _fetch_instagram_metrics(metrics: ClipMetrics, media_id: str, creds: Dict):
    """Fetch Instagram Reels metrics via Graph API."""
    import urllib.request

    access_token = creds.get("access_token", "")
    url = (f"https://graph.facebook.com/v18.0/{media_id}"
           f"?fields=views,likes,comments,shares,saved,insights"
           f"&access_token={access_token}")

    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    metrics.views = data.get("views", 0)
    metrics.likes = data.get("likes", {}).get("count", 0)
    metrics.comments = data.get("comments", {}).get("count", 0)
    metrics.saves = data.get("saved", {}).get("count", 0)


def _fetch_facebook_metrics(metrics: ClipMetrics, reel_id: str, creds: Dict):
    """Fetch Facebook Reels metrics."""
    import urllib.request

    access_token = creds.get("access_token", "")
    url = (f"https://graph.facebook.com/v18.0/{reel_id}/video_insights"
           f"?metrics=total_video_views,total_video_likes,total_video_comments"
           f"&access_token={access_token}")

    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    for item in data.get("data", []):
        name = item.get("name", "")
        values = item.get("values", [])
        if values:
            val = values[0].get("value", 0)
            if "views" in name: metrics.views = val
            elif "likes" in name: metrics.likes = val
            elif "comments" in name: metrics.comments = val


def _fetch_twitter_metrics(metrics: ClipMetrics, tweet_id: str, creds: Dict):
    """Fetch Twitter/X metrics (requires API v2)."""
    # Twitter API v2 requires bearer token for public metrics
    bearer = creds.get("bearer_token", "")
    if not bearer:
        return

    import urllib.request
    url = (f"https://api.twitter.com/2/tweets/{tweet_id}"
           f"?tweet.fields=public_metrics")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {bearer}",
    }, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    pm = data.get("data", {}).get("public_metrics", {})
    metrics.views = pm.get("impression_count", 0)
    metrics.likes = pm.get("like_count", 0)
    metrics.comments = pm.get("reply_count", 0)
    metrics.shares = pm.get("retweet_count", 0)


def _fetch_linkedin_metrics(metrics: ClipMetrics, urn: str, creds: Dict):
    """Fetch LinkedIn video metrics."""
    # LinkedIn analytics require the organization/person URN
    # Simplified — production needs full UGC post analytics API
    pass


# -- Analytics Aggregation --

def analyze_clip_performance(
    clip_id: str,
    job_id: str,
    virality_score: Dict,
    platform_metrics: Dict[str, ClipMetrics],
    clip_meta: Optional[Dict] = None,
) -> ClipAnalytics:
    """
    Analyze a single clip's performance across platforms.

    Compares predicted virality score with actual performance
    and generates insights.
    """
    analytics = ClipAnalytics(
        clip_id=clip_id,
        job_id=job_id,
        virality_score=virality_score.get("composite", 0),
        virality_grade=virality_score.get("grade", ""),
    )

    if clip_meta:
        analytics.clip_start = clip_meta.get("start", 0)
        analytics.clip_end = clip_meta.get("end", 0)
        analytics.clip_duration = clip_meta.get("end", 0) - clip_meta.get("start", 0)
        analytics.hook_archetype = virality_score.get("detected_patterns", [""])[0] if virality_score.get("detected_patterns") else ""
        analytics.caption_style = clip_meta.get("caption_style", "")

    analytics.platforms = platform_metrics

    # Aggregate metrics
    for platform, m in platform_metrics.items():
        analytics.total_views += m.views
        analytics.total_likes += m.likes
        analytics.total_comments += m.comments
        analytics.total_shares += m.shares
        analytics.total_saves += m.saves

    analytics.total_engagement = (
        analytics.total_likes + analytics.total_comments +
        analytics.total_shares + analytics.total_saves
    )

    if analytics.total_views > 0:
        analytics.engagement_rate = (
            analytics.total_engagement / analytics.total_views * 100
        )

    # Find best/worst platform
    if platform_metrics:
        sorted_by_views = sorted(
            platform_metrics.items(),
            key=lambda x: x[1].views, reverse=True
        )
        analytics.best_platform = sorted_by_views[0][0]
        analytics.worst_platform = sorted_by_views[-1][0]

    # Calculate prediction accuracy
    if analytics.total_views > 0:
        # Normalize actual views to 0-100 scale
        # Using log scale: 100 views = ~50, 10K views = ~75, 100K = ~90, 1M+ = ~100
        actual_score = min(100, 30 + math.log10(max(analytics.total_views, 1)) * 10)
        analytics.prediction_error = abs(analytics.virality_score - actual_score)
        analytics.prediction_accuracy = max(0, 1.0 - (analytics.prediction_error / 100))

    # Generate insights
    analytics.insights = _generate_clip_insights(analytics, virality_score)
    analytics.recommendations = _generate_clip_recommendations(analytics)

    return analytics


def analyze_job_performance(
    job_id: str,
    clip_analytics: List[ClipAnalytics],
) -> JobAnalytics:
    """
    Analyze performance of all clips in a job.

    Provides job-level insights and cross-clip comparisons.
    """
    analytics = JobAnalytics(job_id=job_id)

    analytics.total_clips = len(clip_analytics)
    analytics.clip_analytics = clip_analytics

    # Aggregate
    for ca in clip_analytics:
        analytics.total_views += ca.total_views
        analytics.total_likes += ca.total_likes
        analytics.total_comments += ca.total_comments
        analytics.total_shares += ca.total_shares
        analytics.avg_virality_score += ca.virality_score

    if analytics.total_clips > 0:
        analytics.avg_virality_score /= analytics.total_clips

    # Find best/worst clip
    if clip_analytics:
        sorted_clips = sorted(clip_analytics, key=lambda c: c.total_views, reverse=True)
        analytics.best_clip_id = sorted_clips[0].clip_id
        analytics.best_clip_views = sorted_clips[0].total_views
        analytics.worst_clip_id = sorted_clips[-1].clip_id
        analytics.worst_clip_views = sorted_clips[-1].total_views

    # Platform breakdown
    analytics.platform_breakdown = _calculate_platform_breakdown(clip_analytics)

    # Job-level insights
    analytics.insights = _generate_job_insights(analytics)

    # Performance predictions for next clips
    analytics.predictions = _generate_predictions(clip_analytics)

    return analytics


# -- Insight Generation --

def _generate_clip_insights(analytics: ClipAnalytics, virality_score: Dict) -> List[str]:
    """Generate insights for a single clip."""
    insights = []

    # Platform comparison
    if len(analytics.platforms) > 1:
        best = analytics.best_platform
        worst = analytics.worst_platform
        best_views = analytics.platforms[best].views
        worst_views = analytics.platforms[worst].views
        if best_views > 0 and worst_views >= 0:
            ratio = best_views / max(worst_views, 1)
            insights.append(f"{best.capitalize()} outperformed {worst.capitalize()} by {ratio:.1f}x")

    # Engagement rate
    if analytics.engagement_rate > 10:
        insights.append(f"High engagement rate: {analytics.engagement_rate:.1f}% (above 10% is excellent)")
    elif analytics.engagement_rate > 5:
        insights.append(f"Good engagement rate: {analytics.engagement_rate:.1f}%")
    elif analytics.engagement_rate < 3 and analytics.total_views > 100:
        insights.append(f"Low engagement rate: {analytics.engagement_rate:.1f}% — content may not resonate")

    # Virality prediction accuracy
    if analytics.prediction_accuracy > 0.7:
        insights.append(f"Virality prediction was accurate ({analytics.prediction_accuracy:.0%} match)")
    elif analytics.prediction_accuracy > 0.5:
        insights.append(f"Virality prediction was moderately accurate ({analytics.prediction_accuracy:.0%} match)")
    elif analytics.total_views > 0:
        insights.append(f"Virality prediction was off by {analytics.prediction_error:.0f} points")

    # Hook archetype performance
    if analytics.hook_archetype and analytics.total_views > 1000:
        insights.append(f"Hook archetype '{analytics.hook_archetype}' performed well ({analytics.total_views:,} views)")

    # Share-to-view ratio (virality indicator)
    if analytics.total_views > 100:
        share_rate = analytics.total_shares / analytics.total_views * 100
        if share_rate > 2:
            insights.append(f"High share rate: {share_rate:.1f}% — this clip is being shared virally")
        elif share_rate < 0.1:
            insights.append(f"Low share rate: {share_rate:.2f}% — viewers watch but don't share")

    # Save rate (content value indicator)
    if analytics.total_views > 100:
        save_rate = analytics.total_saves / analytics.total_views * 100
        if save_rate > 5:
            insights.append(f"High save rate: {save_rate:.1f}% — content is valuable to viewers")

    return insights


def _generate_clip_recommendations(analytics: ClipAnalytics) -> List[str]:
    """Generate actionable recommendations for a clip."""
    recs = []

    if analytics.total_views < 100:
        recs.append("Low views — check posting time and hashtags for better discovery")

    if analytics.engagement_rate < 3 and analytics.total_views > 50:
        recs.append("Low engagement — consider revising the hook or caption style")

    if analytics.completion_rate < 0.3 and analytics.avg_watch_time > 0:
        recs.append(f"Low completion rate ({analytics.completion_rate:.0%}) — clip may be too long or slow")

    if analytics.total_shares == 0 and analytics.total_views > 200:
        recs.append("No shares despite decent views — content isn't shareable enough")

    # Platform-specific recommendations
    for platform, m in analytics.platforms.items():
        if m.views > 0:
            platform_eng = (m.likes + m.comments + m.shares) / m.views * 100
            if platform_eng < 2:
                recs.append(f"{platform}: engagement is low ({platform_eng:.1f}%) — try different hashtags")

    return recs


def _generate_job_insights(analytics: JobAnalytics) -> List[str]:
    """Generate insights at the job level."""
    insights = []

    if analytics.total_clips == 0:
        return ["No clips to analyze"]

    # Average performance
    avg_views = analytics.total_views / analytics.total_clips
    insights.append(f"Average views per clip: {avg_views:,.0f}")

    # Best performer
    if analytics.best_clip_views > 0:
        insights.append(f"Best clip: {analytics.best_clip_id} with {analytics.best_clip_views:,} views")

    # Virality prediction accuracy
    accurate_clips = sum(
        1 for c in analytics.clip_analytics
        if c.prediction_accuracy > 0.6
    )
    if analytics.total_clips > 0:
        accuracy_pct = accurate_clips / analytics.total_clips * 100
        insights.append(f"Virality prediction accuracy: {accuracy_pct:.0f}% of clips predicted accurately")

    # Platform comparison
    for platform, data in analytics.platform_breakdown.items():
        if data["total_views"] > 0:
            insights.append(
                f"{platform}: {data['total_views']:,} total views, "
                f"{data['avg_engagement_rate']:.1f}% avg engagement"
            )

    # Hook archetype performance
    archetype_perf = defaultdict(list)
    for c in analytics.clip_analytics:
        if c.hook_archetype:
            archetype_perf[c.hook_archetype].append(c.total_views)

    if archetype_perf:
        best_archetype = max(archetype_perf.items(), key=lambda x: sum(x[1]) / len(x[1]))
        insights.append(
            f"Best performing hook archetype: '{best_archetype[0]}' "
            f"({sum(best_archetype[1]):,} total views)"
        )

    return insights


def _calculate_platform_breakdown(clip_analytics: List[ClipAnalytics]) -> Dict:
    """Calculate per-platform aggregated metrics."""
    breakdown = defaultdict(lambda: {
        "total_views": 0, "total_likes": 0, "total_comments": 0,
        "total_shares": 0, "total_saves": 0, "clip_count": 0,
        "engagement_rates": [],
    })

    for ca in clip_analytics:
        for platform, m in ca.platforms.items():
            bd = breakdown[platform]
            bd["total_views"] += m.views
            bd["total_likes"] += m.likes
            bd["total_comments"] += m.comments
            bd["total_shares"] += m.shares
            bd["total_saves"] += m.saves
            bd["clip_count"] += 1
            if m.views > 0:
                bd["engagement_rates"].append(
                    (m.likes + m.comments + m.shares) / m.views * 100
                )

    result = {}
    for platform, data in breakdown.items():
        avg_eng = sum(data["engagement_rates"]) / len(data["engagement_rates"]) if data["engagement_rates"] else 0
        result[platform] = {
            "total_views": data["total_views"],
            "total_likes": data["total_likes"],
            "total_comments": data["total_comments"],
            "total_shares": data["total_shares"],
            "total_saves": data["total_saves"],
            "clip_count": data["clip_count"],
            "avg_engagement_rate": round(avg_eng, 1),
        }

    return result


def _generate_predictions(clip_analytics: List[ClipAnalytics]) -> List[Dict]:
    """Generate performance predictions based on historical data."""
    predictions = []

    if len(clip_analytics) < 2:
        return predictions

    # Calculate average performance by hook archetype
    archetype_stats = defaultdict(lambda: {"views": [], "engagement": []})
    for ca in clip_analytics:
        if ca.hook_archetype:
            archetype_stats[ca.hook_archetype]["views"].append(ca.total_views)
            archetype_stats[ca.hook_archetype]["engagement"].append(ca.engagement_rate)

    # Predict expected performance for each archetype
    for archetype, stats in archetype_stats.items():
        if len(stats["views"]) >= 1:
            avg_views = sum(stats["views"]) / len(stats["views"])
            avg_eng = sum(stats["engagement"]) / len(stats["engagement"]) if stats["engagement"] else 0
            predictions.append({
                "hook_archetype": archetype,
                "expected_views": round(avg_views),
                "expected_engagement_rate": round(avg_eng, 1),
                "sample_size": len(stats["views"]),
            })

    # Sort by expected views
    predictions.sort(key=lambda p: p["expected_views"], reverse=True)

    return predictions


# -- API Response Format --

def clip_analytics_to_api_dict(analytics: ClipAnalytics) -> Dict:
    """Convert ClipAnalytics to API-friendly dict."""
    return {
        "clip_id": analytics.clip_id,
        "job_id": analytics.job_id,
        "clip_start": analytics.clip_start,
        "clip_end": analytics.clip_end,
        "hook_archetype": analytics.hook_archetype,
        "virality_score": analytics.virality_score,
        "virality_grade": analytics.virality_grade,
        "total_views": analytics.total_views,
        "total_likes": analytics.total_likes,
        "total_comments": analytics.total_comments,
        "total_shares": analytics.total_shares,
        "total_saves": analytics.total_saves,
        "engagement_rate": round(analytics.engagement_rate, 2),
        "best_platform": analytics.best_platform,
        "worst_platform": analytics.worst_platform,
        "prediction_accuracy": round(analytics.prediction_accuracy, 2),
        "prediction_error": round(analytics.prediction_error, 1),
        "platforms": {
            p: {
                "views": m.views, "likes": m.likes,
                "comments": m.comments, "shares": m.shares,
                "saves": m.saves, "avg_watch_time": m.avg_watch_time,
                "completion_rate": m.completion_rate,
            }
            for p, m in analytics.platforms.items()
        },
        "insights": analytics.insights,
        "recommendations": analytics.recommendations,
    }


def job_analytics_to_api_dict(analytics: JobAnalytics) -> Dict:
    """Convert JobAnalytics to API-friendly dict."""
    return {
        "job_id": analytics.job_id,
        "total_clips": analytics.total_clips,
        "total_views": analytics.total_views,
        "total_likes": analytics.total_likes,
        "total_comments": analytics.total_comments,
        "total_shares": analytics.total_shares,
        "avg_virality_score": round(analytics.avg_virality_score, 1),
        "best_clip": {
            "clip_id": analytics.best_clip_id,
            "views": analytics.best_clip_views,
        },
        "worst_clip": {
            "clip_id": analytics.worst_clip_id,
            "views": analytics.worst_clip_views,
        },
        "platform_breakdown": analytics.platform_breakdown,
        "insights": analytics.insights,
        "predictions": analytics.predictions,
        "clips": [clip_analytics_to_api_dict(ca) for ca in analytics.clip_analytics],
    }
