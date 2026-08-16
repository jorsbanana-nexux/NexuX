from __future__ import annotations
from typing import Any, Iterable, Mapping, Sequence

def _iou(a: Mapping[str, Any], b: Mapping[str, Any]) -> float:
    s=max(float(a.get('start',0)),float(b.get('start',0))); e=min(float(a.get('end',0)),float(b.get('end',0))); inter=max(0,e-s); union=max(float(a.get('end',0)),float(b.get('end',0)))-min(float(a.get('start',0)),float(b.get('start',0))); return inter/union if union>0 else 0.0

def top1_iou(predicted: Sequence[Mapping[str,Any]], reference: Sequence[Mapping[str,Any]]) -> float:
    return max((_iou(predicted[0],r) for r in reference),default=0.0) if predicted else 0.0

def recall_at_k(predicted: Sequence[Mapping[str,Any]], reference: Sequence[Mapping[str,Any]], k:int=5, threshold:float=.5)->float:
    if not reference:return 0.0
    pool=list(predicted)[:max(0,int(k))]; return sum(any(_iou(p,r)>=threshold for p in pool) for r in reference)/len(reference)

def mean_best_iou(predicted: Sequence[Mapping[str,Any]], reference: Sequence[Mapping[str,Any]])->float:
    return sum(max((_iou(p,r) for p in predicted),default=0.0) for r in reference)/len(reference) if reference else 0.0

def duration_compliance(clips: Iterable[Mapping[str,Any]], target:float, tolerance:float=.15)->float:
    cs=list(clips)
    if not cs or target<=0:return 0.0
    return sum(abs(float(c.get('duration',float(c.get('end',0))-float(c.get('start',0))))-target)<=target*tolerance for c in cs)/len(cs)

def editorial_failure_rate(cases:Iterable[Mapping[str,Any]])->float:
    cs=list(cases); return sum(bool(c.get('failed',False)) for c in cs)/len(cs) if cs else 0.0

def aggregate_metrics(reports:Iterable[Mapping[str,Any]])->dict[str,float]:
    rs=list(reports); keys=('top1_iou','recall_at_k','mean_best_iou','duration_compliance','human_preference','editorial_failure_rate','technical_failure_rate','caption_accuracy','av_sync_failure_rate')
    return {k:sum(float(r[k]) for r in rs if k in r)/len([r for r in rs if k in r]) for k in keys if any(k in r for r in rs)}
