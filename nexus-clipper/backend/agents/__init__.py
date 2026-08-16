"""NexuX 25-agent compatibility/augmentation matrix."""

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
from .agent_11_scene_segmenter import SceneSegmenter
from .agent_12_subject_tracker import SubjectTracker
from .agent_13_quality_checker import VisualQualityChecker
from .agent_14_lip_sync import LipSyncModifier
from .agent_15_broll_blocker import BrollBlocker
from .agent_16_subtitle_designer import SubtitleDesigner
from .agent_17_sound_designer import SoundDesigner
from .agent_18_music_selector import MusicSelector
from .agent_19_transition_ai import TransitionAI
from .agent_20_professional_editor import ProfessionalEditor
from .agent_21_quality_inspector import QualityInspector
from .agent_22_audience_predictor import AudiencePredictor
from .agent_23_auto_improver import AutoImprover
from .agent_24_omni_exporter import OmniExporter
from .agent_25_seo_generator import SEOGenerator
from .capability_matrix import AGENT_MATRIX, get_agent_matrix, summary

AGENT_REGISTRY = {
    f"agent_{index:02d}": cls
    for index, cls in enumerate([
        MasterBrain, URLFetcher, KeywordOptimizer, ContentPlanner, CompetitorAnalyzer,
        NarrationWriter, VoiceCloner, EmotionController, Spatial8DAudio, BreathInjector,
        SceneSegmenter, SubjectTracker, VisualQualityChecker, LipSyncModifier, BrollBlocker,
        SubtitleDesigner, SoundDesigner, MusicSelector, TransitionAI, ProfessionalEditor,
        QualityInspector, AudiencePredictor, AutoImprover, OmniExporter, SEOGenerator,
    ], 1)
}

__all__ = ["AGENT_REGISTRY", "AGENT_MATRIX", "get_agent_matrix", "summary"]
