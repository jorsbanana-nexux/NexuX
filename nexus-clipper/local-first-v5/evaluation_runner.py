from __future__ import annotations
from typing import Any, Sequence
from benchmark_contract import BenchmarkCase, BenchmarkReport, build_benchmark_report
from benchmark_metrics import aggregate_metrics, duration_compliance, mean_best_iou, recall_at_k, top1_iou
from human_preference import PreferenceRecord, preference_distribution

def evaluate_case(case:BenchmarkCase)->dict[str,Any]:
    case.validate(); p=list(case.clips); r=list(case.reference_clips); target=float(case.metadata.get('target_duration',0) or 0)
    return {'case_id':case.case_id,'system':case.system,'top1_iou':top1_iou(p,r),'recall_at_k':recall_at_k(p,r,k=int(case.metadata.get('k',5) or 5)),'mean_best_iou':mean_best_iou(p,r),'duration_compliance':duration_compliance(p,target) if target>0 else 0.0,'editorial_failure_rate':float(bool(case.metadata.get('editorial_failure',False))),'technical_failure_rate':float(bool(case.metadata.get('technical_failure',False))),'caption_accuracy':max(0,min(1,float(case.metadata.get('caption_accuracy',0) or 0))),'av_sync_failure_rate':float(bool(case.metadata.get('av_sync_failure',False)))}

def run_benchmark(cases:Sequence[BenchmarkCase],run_id:str,*,preferences:Sequence[PreferenceRecord]=())->BenchmarkReport:
    reports=[evaluate_case(c) for c in cases]; metrics=aggregate_metrics(reports); dist=preference_distribution(list(preferences));
    if dist: metrics['human_preference']=dist.get('nexux',0.0)
    return build_benchmark_report(run_id,metrics,case_count=len(cases),metadata={'human_preference_distribution':dist})

def compare_systems(cases:Sequence[BenchmarkCase]):
    grouped={}
    for c in cases: grouped.setdefault(c.system,[]).append(c)
    return {s:run_benchmark(v,f'comparison-{s}') for s,v in grouped.items()}
