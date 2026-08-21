"""
NexuX V9.5 — Podcast Analyzer (Mode 1 Enhanced)
===================================================
Specialized analysis for podcast/interview/talk-show content.

Podcasts are different from general videos:
- Multi-speaker conversations with turn-taking
- Long monologues broken by host questions
- Key moments are often punchlines, revelations, or heated debates
- Natural chapter boundaries exist (topic shifts)

This module adds podcast-specific intelligence:
1. Topic segmentation — detect topic changes
2. Punchline extraction — find the "money quote" in each segment
3. Heat detection — find moments of high energy/conflict
4. Story arc detection — find narrative anecdotes
5. Question-answer pairing — find engaging Q&A exchanges
6. Filler removal — identify and mark filler words for cutting
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

log = logging.getLogger("nexus.podcast_analyzer")


# ── Filler words (EN + ID) ──
FILLER_WORDS = {
    "en": ["um", "uh", "er", "ah", "hmm", "you know", "i mean", "like", "basically",
           "essentially", "sort of", "kind of", "right", "so yeah", "anyway"],
    "id": ["eh", "um", "ah", "yang", "itu", "kan", "deh", "sih", "nah", "ya", "gitu",
           "terus", "trus", "kayak", "kayaknya", "terus", "anuu", "emm"],
}

# Topic transition signals
TOPIC_TRANSITION_SIGNALS = [
    # English
    r"\b(let'?s talk about|moving on to|next topic|shifting gears|on another note|speaking of|turning to)\b",
    r"\b(let me ask you|i want to ask|here'?s an interesting|this reminds me)\b",
    r"\b(changing subject|different topic|another thing|one more thing)\b",
    # Indonesian
    r"\b(ngomong soal|lanjut ke|topik selanjutnya|ngomongin|balik ke|sebenernya soal)\b",
    r"\b(aku mau nanya|aku pengen tanya|menarik nih|ini ingetin)\b",
    r"\b(ganti topik|hal lain|satu lagi|yang satu ini)\b",
]

# Punchline signals (the "money quote")
PUNCHLINE_SIGNALS = [
    # English
    r"\b(the point is|here'?s the thing|what it comes down to|bottom line|the truth is)\b",
    r"\b(and that'?s when|it turns out|the crazy part|what most people don'?t know)\b",
    r"\b(so the lesson|the takeaway|what i learned|the moral is)\b",
    # Indonesian
    r"\b(intinya|yang penting|pokoknya|jangan lupa|pelajarannya)\b",
    r"\b(ternyata|eh ternyata|yang gila adalah|yang kebanyakan orang gak tau)\b",
    r"\b(percikan|kesimpulan|hikmahnya|pelajaran yang aku dapat)\b",
]

# Heat/conflict signals
HEAT_SIGNALS = [
    r"\b(no no no|wait wait|hold on|that'?s wrong|i disagree|bullshit|nonsense)\b",
    r"\b(nggak nggak|tunggu tunggu|salah itu|gak setuju|omong kosong|ngaco)\b",
    r"\b(!{2,}|CAPS.{5,})\b",  # Multiple exclamations or all-caps shouting
    r"\b(you'?re wrong|that'?s not true|absolutely not)\b",
    r"\b(kamu salah|itu nggak benar|jelas nggak|masa sih)\b",
]

# Story/anecdote launch signals
STORY_SIGNALS = [
    r"\b(so (this|there|i was|one time)|a few years ago|back when|i remember when)\b",
    r"\b(jadi (ini|ada|waktu itu|dulu|pernah)|beberapa tahun lalu|dulu ceritanya|aku inget)\b",
    r"\b(let me tell you|story time|this happened|so basically)\b",
    r"\b(cerita nih|ini kejadian|jadi gini|begini ceritanya)\b",
]


@dataclass
class PodcastSegment:
    """A topic-coherent segment of a podcast."""
    start: float
    end: float
    topic: str = ""
    topic_confidence: float = 0.0
    speakers: List[str] = field(default_factory=list)
    speaker_count: int = 0
    turns: int = 0
    heat_score: float = 0.0
    has_punchline: bool = False
    punchline_text: str = ""
    has_story: bool = False
    has_qa_pair: bool = False
    question: str = ""
    answer: str = ""
    filler_ratio: float = 0.0
    text: str = ""
    clip_worthiness: float = 0.0  # 0-100


def analyze_podcast(
    segments: List[Dict],
    total_duration: float,
    target_duration: int = 60,
    max_clips: int = 10,
) -> List[Dict]:
    """
    Analyze a podcast transcript to find the best clips.
    
    This is podcast-specific analysis that goes beyond generic viral detection:
    1. Segment the podcast into topics
    2. Find punchlines within each topic
    3. Score heat/conflict moments
    4. Detect story arcs
    5. Find engaging Q&A pairs
    6. Calculate filler ratio (for removal)
    7. Score overall clip-worthiness
    
    Returns list of clip candidates with enhanced podcast metadata.
    """
    if not segments:
        return []
    
    log.info(f"[PodcastAnalyzer] Analyzing {len(segments)} segments, duration: {total_duration:.0f}s")
    
    # 1. Topic segmentation
    topic_segments = _segment_by_topic(segments)
    log.info(f"[PodcastAnalyzer] Found {len(topic_segments)} topic segments")
    
    # 2. Analyze each topic segment
    candidates = []
    for topic_seg in topic_segments:
        topic_segs = topic_seg["segments"]
        if len(topic_segs) < 2:
            continue
        
        # Analyze punchlines, heat, stories, Q&A
        analysis = _analyze_topic_segment(topic_segs)
        
        # Generate clip candidates from this topic
        topic_clips = _generate_clips_from_topic(
            topic_seg, analysis, target_duration, total_duration
        )
        candidates.extend(topic_clips)
    
    # 3. Also scan with sliding window for clips that span topic boundaries
    # (sometimes the best clip starts at the end of one topic and finishes in another)
    boundary_clips = _scan_topic_boundaries(segments, topic_segments, target_duration, total_duration)
    candidates.extend(boundary_clips)
    
    # 4. Deduplicate and sort
    candidates = _deduplicate_clips(candidates)
    candidates.sort(key=lambda c: c.get("clip_worthiness", c.get("score", 0)), reverse=True)
    
    log.info(f"[PodcastAnalyzer] Generated {len(candidates)} candidates, top score: {candidates[0].get('clip_worthiness', 0):.1f}" if candidates else "No candidates")
    
    return candidates[:max_clips]


def _segment_by_topic(segments: List[Dict]) -> List[Dict]:
    """Segment the podcast by topic changes."""
    topics = []
    current_topic = {"start": 0, "end": 0, "segments": [], "topic": "Introduction"}
    
    for i, seg in enumerate(segments):
        text = seg.get("text", "").strip()
        if not text:
            continue
        
        # Check for topic transition
        is_transition = any(re.search(p, text, re.I) for p in TOPIC_TRANSITION_SIGNALS)
        
        if is_transition and len(current_topic["segments"]) >= 3:
            # Close current topic
            current_topic["end"] = seg.get("start", current_topic["end"])
            topics.append(current_topic)
            # Start new topic
            current_topic = {
                "start": seg.get("start", 0),
                "end": 0,
                "segments": [seg],
                "topic": text[:80],
            }
        else:
            current_topic["segments"].append(seg)
        
        current_topic["end"] = seg.get("end", current_topic["end"])
    
    # Don't forget the last topic
    if current_topic["segments"]:
        topics.append(current_topic)
    
    return topics


def _analyze_topic_segment(segs: List[Dict]) -> Dict:
    """Analyze a topic segment for punchlines, heat, stories, Q&A."""
    all_text = " ".join(s.get("text", "") for s in segs).strip()
    all_lower = all_text.lower()
    
    # Punchline detection
    punchlines = []
    for seg in segs:
        text = seg.get("text", "").strip()
        for pattern in PUNCHLINE_SIGNALS:
            if re.search(pattern, text, re.I):
                punchlines.append({
                    "text": text[:150],
                    "time": seg.get("start", 0),
                })
                break
    
    # Heat detection
    heat_score = 0.0
    for pattern in HEAT_SIGNALS:
        if re.search(pattern, all_lower):
            heat_score += 25.0
    heat_score = min(100.0, heat_score)
    
    # Story detection
    has_story = any(re.search(p, all_lower) for p in STORY_SIGNALS)
    
    # Q&A detection (question followed by answer from different speaker)
    qa_pairs = []
    for i in range(len(segs) - 1):
        curr = segs[i].get("text", "").strip()
        next_seg = segs[i + 1].get("text", "").strip()
        curr_speaker = segs[i].get("speaker", "SPEAKER_00")
        next_speaker = segs[i + 1].get("speaker", "SPEAKER_01")
        
        if curr.endswith('?') and curr_speaker != next_speaker and next_seg:
            qa_pairs.append({
                "question": curr[:100],
                "answer": next_seg[:100],
                "question_time": segs[i].get("start", 0),
                "answer_time": segs[i + 1].get("start", 0),
            })
    
    # Filler ratio
    words = all_text.split()
    filler_count = 0
    for w in words:
        w_lower = w.lower().strip(".,!?")
        if w_lower in FILLER_WORDS["en"] or w_lower in FILLER_WORDS["id"]:
            filler_count += 1
    filler_ratio = filler_count / max(len(words), 1)
    
    # Speaker info
    speakers = list(set(s.get("speaker", "SPEAKER_00") for s in segs))
    turns = sum(1 for i in range(1, len(segs))
                if segs[i].get("speaker") != segs[i-1].get("speaker"))
    
    return {
        "punchlines": punchlines,
        "heat_score": heat_score,
        "has_story": has_story,
        "qa_pairs": qa_pairs,
        "filler_ratio": filler_ratio,
        "speaker_count": len(speakers),
        "turns": turns,
        "all_text": all_text,
    }


def _generate_clips_from_topic(
    topic: Dict, analysis: Dict, target_duration: int, total_duration: float
) -> List[Dict]:
    """Generate clip candidates from a topic segment."""
    clips = []
    segs = topic["segments"]
    topic_start = topic["start"]
    topic_end = topic["end"]
    topic_duration = topic_end - topic_start
    
    # If topic is shorter than target, the whole topic is one clip
    if topic_duration <= target_duration * 1.2:
        clip = _make_clip_candidate(topic_start, topic_end, topic, analysis, total_duration)
        clips.append(clip)
        return clips
    
    # If there are punchlines, center clips around them
    for punch in analysis["punchlines"]:
        punch_time = punch["time"]
        # Clip centered on punchline (punchline at ~40% into clip for buildup)
        clip_start = max(0, punch_time - target_duration * 0.3)
        clip_end = min(topic_end, clip_start + target_duration)
        
        # Adjust if clip would be too short
        if clip_end - clip_start < target_duration * 0.5:
            clip_start = max(0, clip_end - target_duration)
        
        clip = _make_clip_candidate(clip_start, clip_end, topic, analysis, total_duration,
                                     punchline=punch)
        clips.append(clip)
    
    # If there are Q&A pairs, create clips around them
    for qa in analysis["qa_pairs"]:
        qa_start = qa["question_time"]
        qa_end = min(qa["answer_time"] + target_duration * 0.5, topic_end)
        if qa_end - qa_start < target_duration * 0.5:
            qa_end = min(qa_start + target_duration, topic_end)
        
        clip = _make_clip_candidate(qa_start, qa_end, topic, analysis, total_duration, qa=qa)
        clips.append(clip)
    
    # If no specific moments found, create a clip from the most active part
    if not clips:
        # Use the middle of the topic (usually most developed)
        mid = (topic_start + topic_end) / 2
        clip_start = max(topic_start, mid - target_duration / 2)
        clip_end = min(topic_end, clip_start + target_duration)
        clip = _make_clip_candidate(clip_start, clip_end, topic, analysis, total_duration)
        clips.append(clip)
    
    return clips


def _scan_topic_boundaries(
    segments: List[Dict],
    topics: List[Dict],
    target_duration: int,
    total_duration: float,
) -> List[Dict]:
    """Scan for good clips that span topic boundaries."""
    clips = []
    
    for i in range(len(topics) - 1):
        # Boundary between topic i and topic i+1
        boundary_time = topics[i]["end"]
        
        # Create a clip that ends at the boundary (climax of previous topic)
        clip_end = boundary_time + 3  # Small overlap
        clip_start = max(0, clip_end - target_duration)
        
        boundary_segs = [s for s in segments if s.get("start", 0) < clip_end and s.get("end", 0) > clip_start]
        if len(boundary_segs) >= 3:
            analysis = _analyze_topic_segment(boundary_segs)
            clip = _make_clip_candidate(clip_start, clip_end, topics[i], analysis, total_duration)
            clip["boundary_clip"] = True
            clips.append(clip)
    
    return clips


def _make_clip_candidate(
    start: float, end: float, topic: Dict, analysis: Dict,
    total_duration: float, punchline: Dict = None, qa: Dict = None,
) -> Dict:
    """Create a clip candidate with podcast-specific scoring."""
    clip_duration = end - start
    
    # Clip worthiness score (0-100)
    worth = 50.0  # Base
    
    # Punchline bonus
    if punchline:
        worth += 20.0
    
    # Heat bonus
    worth += analysis["heat_score"] * 0.15
    
    # Story bonus
    if analysis["has_story"]:
        worth += 10.0
    
    # Q&A bonus
    if qa:
        worth += 12.0
    
    # Multi-speaker bonus
    if analysis["speaker_count"] >= 2:
        worth += 8.0
    
    # Turn-taking bonus
    if 3 <= analysis["turns"] <= 15:
        worth += 7.0
    
    # Filler penalty
    worth -= analysis["filler_ratio"] * 30.0
    
    # Duration bonus (sweet spot: 30-60s)
    if 30 <= clip_duration <= 60:
        worth += 5.0
    
    worth = max(0.0, min(100.0, worth))
    
    result = {
        "start": round(start, 2),
        "end": round(end, 2),
        "duration": round(clip_duration, 1),
        "score": round(worth / 100, 4),  # Normalized for pipeline compatibility
        "clip_worthiness": round(worth, 1),
        "topic": topic.get("topic", "")[:80],
        "speakers": analysis["speaker_count"],
        "turns": analysis["turns"],
        "heat_score": round(analysis["heat_score"], 1),
        "has_punchline": bool(punchline),
        "punchline_text": punchline["text"] if punchline else "",
        "has_story": analysis["has_story"],
        "has_qa": bool(qa),
        "filler_ratio": round(analysis["filler_ratio"], 3),
        "text_preview": analysis["all_text"][:300],
    }
    
    return result


def _deduplicate_clips(clips: List[Dict]) -> List[Dict]:
    """Remove overlapping clips, keeping the best one."""
    clips.sort(key=lambda c: c.get("clip_worthiness", 0), reverse=True)
    taken = []
    result = []
    
    for c in clips:
        c_start = c["start"]
        c_end = c["end"]
        overlaps = any(
            not (c_end <= t[0] + 5 or c_start >= t[1] - 5)
            for t in taken
        )
        if overlaps:
            continue
        taken.append((c_start, c_end))
        result.append(c)
    
    return result


def detect_filler_words(text: str, language: str = "en") -> List[Dict]:
    """
    Detect filler words in text and return their positions.
    
    Used by the render pipeline to mark filler words for removal/muting.
    
    Returns:
        [{"word": "um", "start": 1.2, "end": 1.5, "language": "en"}, ...]
    """
    words = text.split()
    fillers = []
    
    filler_set = FILLER_WORDS.get(language, FILLER_WORDS["en"]) | FILLER_WORDS.get("id", set())
    
    for i, word in enumerate(words):
        w_lower = word.lower().strip(".,!?")
        if w_lower in filler_set:
            fillers.append({
                "word": word,
                "position": i,
                "language": language,
            })
    
    return fillers
