from __future__ import annotations
from typing import Any, Mapping, Sequence

def _lines(text:str,max_chars:int=34):
    words=str(text or '').split(); lines=[]; cur=[]; n=0
    for w in words:
        if cur and n+1+len(w)>max_chars: lines.append(' '.join(cur)); cur=[w]; n=len(w)
        else: cur.append(w); n+=len(w)+(1 if len(cur)>1 else 0)
    if cur: lines.append(' '.join(cur))
    return lines[:2] or ['']

def plan_caption_direction(segments:Sequence[Mapping[str,Any]]|None=None,*,style='dynamic',language='auto',max_chars=34):
    items=[{'start':float(s.get('start',0)), 'end':float(s.get('end',0)), 'text':str(s.get('text','')).strip(), 'lines':_lines(str(s.get('text','')),max_chars), 'emphasis':[]} for s in (segments or [])]
    return {'director':'caption','style':style,'language':language,'safe_area':{'top':.08,'bottom':.12,'left':.06,'right':.06},'max_lines':2,'items':items,'quality':{'readability_target':.9,'caption_overlap_forbidden':True,'face_occlusion_target':0.0}}
