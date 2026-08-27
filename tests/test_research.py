import pytest
from unittest.mock import MagicMock, patch
from src.research.wikipedia_client import WikipediaClient
from src.research.source_validator import SourceValidator
from src.research.research_manager import ResearchManager

def test_concept_extraction():
    client = WikipediaClient()
    topic = "Why Does Bioluminescent Ocean Waves Happen?"
    concepts = client.extract_search_concepts(topic)
    assert len(concepts) > 0
    for c in concepts:
        assert len(c.split()) <= 4

def test_source_validator_relevant_page():
    validator = SourceValidator()
    topic = "Bioluminescent Ocean Waves"
    page = {
        "title": "Bioluminescence in Ocean Waves",
        "extract": "Bioluminescence is the production and emission of light by a living organism. Marine organisms in ocean waves produce brilliant blue glows."
    }
    is_valid, score, reason = validator.validate_source(topic, page)
    assert is_valid
    assert score >= 0.20

def test_source_validator_weak_page():
    validator = SourceValidator()
    topic = "Bioluminescent Ocean Waves"
    page = {
        "title": "Taxation in Medieval England",
        "extract": "Taxation in medieval England involved various duties and tariffs on agricultural products and feudal lands."
    }
    is_valid, score, reason = validator.validate_source(topic, page)
    assert not is_valid
    assert score < 0.20

def test_research_manager_fallback():
    manager = ResearchManager()
    # Mock wikipedia client search to return empty
    with patch.object(manager.wiki_client, "search_pages", return_value=[]):
        res = manager.research_topic("Why Does Bioluminescent Ocean Waves Happen?", "Nature & Earth")
        assert res["topic"] == "Why Does Bioluminescent Ocean Waves Happen?"
        assert len(res["sources"]) > 0
        assert len(res["facts"]) > 0

def test_research_manager_api_error_handling():
    manager = ResearchManager()
    with patch.object(manager.wiki_client, "search_pages", side_effect=Exception("Network error")):
        res = manager.research_topic("Black Hole Gravity", "Space")
        assert res is not None
        assert len(res["facts"]) > 0
