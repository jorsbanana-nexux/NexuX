"""AGENT_22_AUDIENCE_PREDICTOR - Viral Score Evaluator"""

from utils.logger import get_logger
log = get_logger("agent_22")

class AudiencePredictor:
    async def predict(self, project_data):
        script = project_data.get("script","")
        duration = project_data.get("target_duration",60)
        hook_words = ["stop","wait","hold up","you won't believe","secret","truth"]
        hook_score = sum(1 for w in hook_words if w in script.lower()[:200]) / max(len(hook_words),1)
        viral = round((hook_score*0.35 + 0.25*0.8 + 0.20*0.75 + 0.20*0.85)*100, 1)
        return {"viral_score": min(viral,100), "verdict": "VIRAL_READY" if viral>=85 else "GOOD" if viral>=70 else "NEEDS_IMPROVEMENT"}

audience_predictor = AudiencePredictor()
