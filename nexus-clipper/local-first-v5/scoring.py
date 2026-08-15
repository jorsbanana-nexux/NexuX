from __future__ import annotations

import re
from dataclasses import dataclass, field

QUESTION = re.compile(r"\?|\b(apakah|kenapa|mengapa|bagaimana|what|why|how|can|could|would)\b", re.I)
NUMBER = re.compile(r"\b\d+(?:[.,]\d+)?(?:%|k|m|juta|ribu|million|billion)?\b", re.I)
EMOTIONAL = re.compile(r"\b(gila|luar biasa|takut|marah|sedih|bahagia|rahasia|menakutkan|amazing|crazy|shocking|terrible|love|hate)\b", re.I)
BENEFIT = re.compile(r"\b(cara|tips|rahasia|membantu|bisa|dapat|hasil|untung|benefit|how to|learn|solusi)\b", re.I)
URGENCY = re.compile(r"\b(sekarang|hari ini|segera|jangan|stop|now|today|immediately)\b", re.I)
CONTRAST = re.compile(r"\b(tapi|namun|padahal|justru|sebaliknya|but|however|instead|actually|meskipun)\b", re.I)
CURIOSITY = re.compile(r"\b(ternyata|yang tidak kamu tahu|rahasia|kebenaran|kenyataannya|belum banyak orang tahu|what nobody tells you)\b", re.I)
CONTROVERSY = re.compile(r"\b(salah|bohong|mitos|kontroversi|bodoh|scam|bullshit|wrong|lie|myth)\b", re.I)
SURPRISING = re.compile(r"\b(ternyata|actually|plot twist|surprisingly|tidak menyangka|gak nyangka|unexpected)\b", re.I)
UNUSUAL = re.compile(r"\b(satu-satunya|tidak masuk akal|mustahil|unusual|nobody|jarang|weird|aneh)\b", re.I)

@dataclass
class Score:
    curiosity: float = 0.0
    question: float = 0.0
    controversy: float = 0.0
    emotional: float = 0.0
    surprising: float = 0.0
    number: float = 0.0
    benefit: float = 0.0
    unusual: float = 0.0
    urgency: float = 0.0
    contradiction: float = 0.0
    hook: float = 0.0
    engagement: float = 0.0
    visual: float = 50.0
    clarity: float = 50.0
    duration_fit: float = 0.0
    viral: float = 0.0
    reasons: list[str] = field(default_factory=list)

def _scale(hits: int, denom: float = 2.0) -> float:
    return max(0.0, min(100.0, 100.0 * hits / denom))

def score_text(text: str, opening: str | None = None) -> Score:
    compact = " ".join(text.split())
    lower = compact.lower()
    hook_text = (opening or compact[:240]).lower()
    s = Score(
        curiosity=_scale(len(CURIOSITY.findall(hook_text))),
        question=90.0 if QUESTION.search(hook_text) else 0.0,
        controversy=_scale(len(CONTROVERSY.findall(hook_text))),
        emotional=_scale(len(EMOTIONAL.findall(hook_text)), 3),
        surprising=min(100.0, 55.0 * len(SURPRISING.findall(hook_text))),
        number=_scale(len(NUMBER.findall(hook_text))),
        benefit=_scale(len(BENEFIT.findall(hook_text)), 3),
        unusual=80.0 if UNUSUAL.search(hook_text) else 0.0,
        urgency=_scale(len(URGENCY.findall(hook_text))),
        contradiction=_scale(len(CONTRAST.findall(hook_text))),
    )
    s.hook = (
        s.curiosity * .18 + s.question * .12 + s.controversy * .10 + s.emotional * .12
        + s.surprising * .13 + s.number * .07 + s.benefit * .09 + s.unusual * .08
        + s.urgency * .05 + s.contradiction * .06
    )
    s.engagement = min(100.0, s.question*.32 + s.emotional*.22 + s.controversy*.16 + s.curiosity*.18 + s.contradiction*.12)
    words = max(1, len(compact.split()))
    s.clarity = max(0.0, min(100.0, 100.0 - abs(words - 80) * 0.7))
    for name in ("curiosity", "question", "controversy", "emotional", "surprising", "number", "benefit", "unusual", "urgency", "contradiction"):
        if getattr(s, name) >= 50:
            s.reasons.append(name)
    return s

def duration_fit(seconds: float, minimum: float = 20.0, maximum: float = 60.0) -> float:
    if minimum <= seconds <= maximum:
        center = (minimum + maximum) / 2
        half = (maximum - minimum) / 2
        return max(0.0, 100.0 - abs(seconds-center)/max(half,1)*35)
    if seconds < minimum:
        return max(0.0, 100.0 - (minimum-seconds)*7)
    return max(0.0, 100.0 - (seconds-maximum)*8)

def rank_score(score: Score, duration: float) -> Score:
    score.duration_fit = duration_fit(duration)
    score.viral = max(0.0, min(100.0,
        score.hook*.34 + score.engagement*.28 + score.visual*.16 + score.clarity*.14 + score.duration_fit*.08
    ))
    return score
