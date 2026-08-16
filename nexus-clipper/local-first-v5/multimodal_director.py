from __future__ import annotations
from typing import Any, Mapping
from adaptive_reframing import plan_adaptive_reframe
from audio_director import plan_audio_direction
from caption_director import plan_caption_direction
from visual_director import plan_visual_direction

def build_multimodal_direction(*, vision:Mapping[str,Any]|None=None,audio:Mapping[str,Any]|None=None,transcript:Mapping[str,Any]|None=None,aspect_ratio='9:16',face_tracking=True,auto_zoom=True,caption_style='dynamic'):
    v=dict(vision or {}); a=dict(audio or {}); t=dict(transcript or {})
    visual=plan_visual_direction(subjects=list(v.get('subjects',[]) or []),scenes=list(v.get('scenes',[]) or []),aspect_ratio=aspect_ratio,face_tracking=face_tracking,auto_zoom=auto_zoom)
    audio_plan=plan_audio_direction(a.get('profile',a),speech_protection=True,music_enabled=False)
    reframe=plan_adaptive_reframe(list(v.get('subject_observations',v.get('observations',[])) or []) or list(v.get('subjects',[]) or []),aspect_ratio=aspect_ratio)
    captions=plan_caption_direction(list(t.get('segments',[]) or []),style=caption_style,language=str(t.get('language','auto')))
    return {'schema_version':'1.0','visual':visual,'audio':audio_plan,'reframe':reframe,'captions':captions,'confidence':round((visual['confidence']+audio_plan['confidence']+reframe['confidence']+(0.8 if captions['items'] else .4))/4,3)}
