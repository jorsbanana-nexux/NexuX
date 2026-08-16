from benchmark_contract import BenchmarkCase, build_benchmark_report
from benchmark_metrics import mean_best_iou, recall_at_k, top1_iou
from evaluation_runner import run_benchmark
from human_preference import build_preference_record, preference_distribution

def clips(): return [{"id":"a","start":0,"end":10,"duration":10},{"id":"b","start":12,"end":22,"duration":10}]
def refs(): return [{"id":"r1","start":1,"end":9,"duration":8}]
def test_metric_engine():
    assert top1_iou(clips(),refs())>0; assert recall_at_k(clips(),refs(),k=1)>0; assert mean_best_iou(clips(),refs())>0
def test_preference_contract():
    r=build_preference_record('r1','e1','case1',['nexux','baseline'],'nexux',dimensions={'story':.9}); assert preference_distribution([r])=={'nexux':1.0}
def test_benchmark_runner():
    c=BenchmarkCase('case1','source1','nexux',tuple(clips()),tuple(refs()),{'target_duration':10,'caption_accuracy':.95}); report=run_benchmark([c],'run1'); assert report.case_count==1 and 'top1_iou' in report.metric_values
def test_report_rejects_unknown_metric():
    try: build_benchmark_report('x',{'bad_metric':1.0},case_count=1)
    except ValueError: return
    raise AssertionError('unknown benchmark metric should fail validation')
