from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"

@dataclass(frozen=True)
class NarrativeBeat:
    kind: str
    start: float
    end: float
    strength: float
    evidence: tuple[str, ...] = ()
    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "start": round(self.start,3), "end": round(self.end,3), "strength": round(self.strength,3), "evidence": list(self.evidence)}

@dataclass(frozen=True)
class NarrativeAssessment:
    schema_version: str
    premise: str
    beats: tuple[NarrativeBeat, ...]
    promise_strength: float
    context_completeness: float
    tension_curve: float
    revelation_strength: float
    payoff_strength: float
    standalone_quality: float
    continuity_risk: float
    premature_cut_risk: float
    unresolved_question_risk: float
    editorial_quality: float
    confidence: float
    recommendation: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    def to_dict(self) -> dict[str, Any]:
        return {"schema_version":self.schema_version,"premise":self.premise,"beats":[b.to_dict() for b in self.beats],"promise_strength":round(self.promise_strength,3),"context_completeness":round(self.context_completeness,3),"tension_curve":round(self.tension_curve,3),"revelation_strength":round(self.revelation_strength,3),"payoff_strength":round(self.payoff_strength,3),"standalone_quality":round(self.standalone_quality,3),"continuity_risk":round(self.continuity_risk,3),"premature_cut_risk":round(self.premature_cut_risk,3),"unresolved_question_risk":round(self.unresolved_question_risk,3),"editorial_quality":round(self.editorial_quality,3),"confidence":round(self.confidence,3),"recommendation":self.recommendation,"reasons":list(self.reasons)}

_Q = re.compile(r"\?|\b(why|how|what|when|where|who|which|can|could|would|should)\b", re.I)
_R = re.compile(r"\b(actually|turns out|the truth is|in fact|i realized|we discovered|the reason is|what happened was)\b", re.I)
_P = re.compile(r"\b(so that means|which means|therefore|that's why|the answer is|finally|in the end|as a result)\b", re.I)
_T = re.compile(r"\b(but|however|except|until|problem|mistake|failed|wrong|never|couldn't|didn't|lost|risk|danger|despite)\b", re.I)
_PROMISE = re.compile(r"\b(i'm going to|i'll show you|here's how|the reason|what you need to know|the secret|the biggest mistake|let me explain)\b", re.I)
_C = re.compile(r"\b(because|therefore|so|which led to|resulted in|after that|then)\b", re.I)

def _clamp(v: float) -> float: return max(0.0, min(1.0, float(v)))
def _words(t: str) -> list[str]: return re.findall(r"[\w']+", t.casefold())
def _overlap(a: str,b: str)->float:
    x,y=set(_words(a)),set(_words(b)); return len(x&y)/max(1,len(x|y)) if x and y else 0.0

def assess_narrative(candidate: Mapping[str,Any], transcript: Mapping[str,Any] | None = None) -> NarrativeAssessment:
    transcript=transcript or {}; start=float(candidate.get("start",0.0)); end=float(candidate.get("end",start)); segs=[dict(s) for s in transcript.get("segments",[]) or [] if float(s.get("end",0.0))>start and float(s.get("start",0.0))<end]
    text=str(candidate.get("text","")).strip();
    if not segs and text: segs=[{"start":start,"end":end,"text":text}]
    first=str(segs[0].get("text","")) if segs else ""; last=str(segs[-1].get("text","")) if segs else ""
    question=bool(_Q.search(text)); revelation=bool(_R.search(text)); payoff=bool(_P.search(text)); tension=bool(_T.search(text)); promise=bool(_PROMISE.search(first)) or bool(_Q.search(first)); words=len(_words(text))
    beats=[]
    if segs: beats.append(NarrativeBeat("setup",float(segs[0].get("start",0)),float(segs[0].get("end",0)),0.8 if promise else 0.55,("opening_context",)))
    if promise: beats.append(NarrativeBeat("promise",float(segs[0].get("start",0)),float(segs[min(1,len(segs)-1)].get("end",0)),0.8,("question_or_promise",)))
    if tension:
        s=segs[max(0,len(segs)//2-1)]; beats.append(NarrativeBeat("tension",float(s.get("start",0)),float(s.get("end",0)),0.72,("conflict_signal",)))
    if revelation:
        s=segs[max(0,len(segs)//2)]; beats.append(NarrativeBeat("revelation",float(s.get("start",0)),float(s.get("end",0)),0.82,("revelation_marker",)))
    if payoff or _C.search(last): beats.append(NarrativeBeat("payoff" if payoff else "consequence",float(segs[-1].get("start",0)),float(segs[-1].get("end",0)),0.84 if payoff else 0.62,("resolution_marker",)))
    context=_clamp(0.35+min(0.4,words/260.0)+(0.15 if promise else 0)+(0.10 if len(segs)>=3 else 0))
    promise_strength=0.55 if promise else 0.20; tension_curve=_clamp(0.25+0.45*tension+0.20*revelation+0.10*(len(beats)>=3)); revelation_strength=_clamp(0.15+0.75*revelation); payoff_strength=_clamp(0.15+0.75*payoff+0.10*bool(_C.search(last)))
    standalone=_clamp(0.40+0.35*context+0.15*payoff_strength+0.10*_overlap(first,last))
    continuity=_clamp((0.55 if len(segs)<2 else 0)+(0.30 if question and not payoff else 0)+(0.20 if first and _overlap(first,last)<0.03 else 0))
    premature=_clamp(0.45*continuity+0.35*(1-payoff_strength)+0.20*(1-context)); unresolved=_clamp((0.70 if question and not payoff else 0)+0.20*(1-context))
    quality=_clamp(0.18*promise_strength+0.16*context+0.16*tension_curve+0.14*revelation_strength+0.18*payoff_strength+0.18*standalone-0.10*continuity-0.10*premature)
    confidence=_clamp(0.45+0.08*min(4,len(beats))+(0.15 if transcript else 0)+(0.10 if words>=20 else 0))
    reasons=[]
    if promise_strength>=0.7: reasons.append("opening creates a promise or question")
    if payoff_strength>=0.7: reasons.append("ending provides a recognizable payoff")
    if tension_curve>=0.65: reasons.append("narrative contains tension or escalation")
    if unresolved>=0.55: reasons.append("opening question may remain unresolved")
    if premature>=0.55: reasons.append("candidate risks ending before resolution")
    if standalone>=0.75: reasons.append("candidate is likely understandable without preceding context")
    recommendation="KEEP" if quality>=0.78 and premature<0.4 else ("REFINE" if quality>=0.58 else "REJECT")
    return NarrativeAssessment(SCHEMA_VERSION,first[:180] or text[:180],tuple(beats),promise_strength,context,tension_curve,revelation_strength,payoff_strength,standalone,continuity,premature,unresolved,quality,confidence,recommendation,tuple(reasons))
