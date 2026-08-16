from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence
SCHEMA_VERSION='1.0'
@dataclass(frozen=True)
class PreferenceRecord:
    record_id:str; evaluator_id:str; case_id:str; ranked_systems:tuple[str,...]; winner:str; dimensions:Mapping[str,float]=field(default_factory=dict); notes:str=''
    def validate(self):
        if not self.record_id or not self.evaluator_id or not self.case_id: raise ValueError('preference identity fields are required')
        if not self.ranked_systems or self.winner not in self.ranked_systems: raise ValueError('winner must occur in ranked_systems')
        if any(not 0<=float(v)<=1 for v in self.dimensions.values()): raise ValueError('preference dimensions must be in [0,1]')
        return self
    def to_dict(self):
        self.validate(); return {'schema_version':SCHEMA_VERSION,'record_id':self.record_id,'evaluator_id':self.evaluator_id,'case_id':self.case_id,'ranked_systems':list(self.ranked_systems),'winner':self.winner,'dimensions':dict(self.dimensions),'notes':self.notes}
def build_preference_record(record_id,evaluator_id,case_id,ranked_systems:Sequence[str],winner,*,dimensions:Mapping[str,float]|None=None,notes=''):
    return PreferenceRecord(record_id,evaluator_id,case_id,tuple(ranked_systems),winner,dict(dimensions or {}),notes).validate()
def preference_distribution(records:Sequence[PreferenceRecord]):
    if not records:return {}
    counts={}
    for r in records: counts[r.winner]=counts.get(r.winner,0)+1
    n=len(records); return {k:v/n for k,v in counts.items()}
