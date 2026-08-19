"""NexuX 20-agent compatibility/augmentation matrix (V8.0).

Removed placeholder agents (11, 12, 13, 20, 21) — their functionality
is handled by canonical engine modules (vision, render, critic, qa).
"""

from .agent_01_master_brain import MasterBrain
from .agent_02_url_fetcher import URLFetcher
from .agent_03_keyword_optimizer import KeywordOptimizer
from .agent_04_content_planner import ContentPlanner
from .agent_05_competitor_analyzer import CompetitorAnalyzer
from .agent_06_narration_writer import NarrationWriter
from .agent_07_voice_cloner import VoiceCloner
from .agent_08_emotion_controller import EmotionController
from .agent_09_spatial_8d_audio import Spatial8DAudio
from .agent_10_breath_injector import BreathInjector
from .agent_14_lip_sync import LipSyncModifier
from .agent_15_broll_blocker import BrollBlocker
from .agent_16_subtitle_designer import SubtitleDesigner
from .agent_17_sound_designer import SoundDesigner
from .agent_18_music_selector import MusicSelector
from .agent_19_transition_ai import TransitionAI
from .agent_22_audience_predictor import AudiencePredictor
from .agent_23_auto_improver import AutoImprover
from .agent_24_omni_exporter import OmniExporter
from .agent_25_seo_generator import SEOGenerator
from .capability_matrix import AGENT_MATRIX, get_agent_matrix, summary

AGENT_REGISTRY = {
    "agent_01": MasterBrain,
    "agent_02": URLFetcher,
    "agent_03": KeywordOptimizer,
    "agent_04": ContentPlanner,
    "agent_05": CompetitorAnalyzer,
    "agent_06": NarrationWriter,
    "agent_07": VoiceCloner,
    "agent_08": EmotionController,
    "agent_09": Spatial8DAudio,
    "agent_10": BreathInjector,
    "agent_14": LipSyncModifier,
    "agent_15": BrollBlocker,
    "agent_16": SubtitleDesigner,
    "agent_17": SoundDesigner,
    "agent_18": MusicSelector,
    "agent_19": TransitionAI,
    "agent_22": AudiencePredictor,
    "agent_23": AutoImprover,
    "agent_24": OmniExporter,
    "agent_25": SEOGenerator,
}

__all__ = ["AGENT_REGISTRY", "AGENT_MATRIX", "get_agent_matrix", "summary"]
