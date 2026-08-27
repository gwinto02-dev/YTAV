import pytest
from pathlib import Path
from unittest.mock import MagicMock
from src.media.visual_planner import VisualPlanner
from src.media.visual_provider import ProviderHealthManager
from src.media.wikimedia_client import WikimediaClient
from src.media.fallback_assets import FallbackAssetsManager
from src.media.asset_validator import AssetValidator
from src.media.media_manager import MediaManager

def test_visual_planner_concise_queries():
    planner = VisualPlanner()
    script = "Imagine discovering that bioluminescent ocean waves glow bright blue in the dark night ocean. Scientists studied dinoflagellates producing light."
    scenes = planner.plan_visuals(script, "Bioluminescent Ocean Waves")
    assert 5 <= len(scenes) <= 8
    for sc in scenes:
        query = sc["visual_concept"]
        assert len(query.split()) <= 6
        assert len(query) <= 50

def test_query_deduplication():
    planner = VisualPlanner()
    script = "Ocean waves glow blue. Ocean waves glow blue. Ocean waves glow blue. Ocean waves glow blue. Ocean waves glow blue."
    scenes = planner.plan_visuals(script, "Ocean Waves")
    queries = [sc["visual_concept"] for sc in scenes]
    assert len(queries) == len(set(queries))

def test_provider_health_manager_circuit_breaker():
    health = ProviderHealthManager(failure_threshold=2)
    health.register_provider("test_provider")
    assert health.is_available("test_provider")
    
    health.record_failure("test_provider", "Network error 1")
    assert health.is_available("test_provider")
    
    health.record_failure("test_provider", "Network error 2")
    # Should now be disabled
    assert not health.is_available("test_provider")

def test_disabled_provider_skipped(tmp_path: Path):
    health = ProviderHealthManager(failure_threshold=2)
    wiki = WikimediaClient(health)
    
    # Mark failure twice
    health.record_failure("wikimedia", "DNS failure")
    health.record_failure("wikimedia", "DNS failure")
    
    out_file = tmp_path / "scene_1.png"
    res = wiki.search_and_download("test query", out_file)
    assert res is None # Skipped immediately without API request

def test_local_fallback_asset_generation(tmp_path: Path):
    fallback = FallbackAssetsManager(tmp_path)
    out_file = tmp_path / "test_fallback.png"
    meta = fallback.get_fallback_asset(1, "deep space black hole", out_file)
    
    assert out_file.exists()
    assert meta["provider"] == "local_fallback"
    
    validator = AssetValidator()
    is_valid, reason, info = validator.validate_asset(out_file)
    assert is_valid
    assert info["width"] == 1080
    assert info["height"] == 1920

def test_media_manager_fallback_chain(tmp_path: Path):
    mm = MediaManager(temp_dir=tmp_path)
    # Simulate API keys absent -> external providers skipped -> falls back to local fallback
    script = "Scientists discovered remarkable natural events in deep frozen lakes."
    scenes = mm.source_scene_visuals(script, "Deep Frozen Lakes")
    
    assert len(scenes) >= 5
    for sc in scenes:
        assert Path(sc["asset_path"]).exists()
        assert sc["asset_metadata"]["provider"] in ["pexels", "pixabay", "wikimedia", "local_fallback"]
