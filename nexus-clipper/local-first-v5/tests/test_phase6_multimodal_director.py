from multimodal_director import build_multimodal_direction

def test_multimodal_director():
    r=build_multimodal_direction(vision={'subjects':[{'id':'s1','confidence':.9,'bbox':{'x':.2,'y':.2,'w':.3,'h':.5}}],'scenes':[{'start':0,'end':10}]},audio={'clarity':88,'speech_density':72,'rhythm':64,'energy':70},transcript={'language':'id','segments':[{'start':0,'end':3,'text':'Ini contoh caption.'}]})
    assert r['visual']['tracking_mode']=='subject_tracking'; assert r['audio']['speech_protection']; assert r['reframe']['mode']=='adaptive_subject_follow'; assert r['captions']['items']; assert 0<=r['confidence']<=1
