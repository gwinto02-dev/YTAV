import pytest
from src.script.script_generator import ScriptGenerator
from src.script.script_validator import ScriptValidator

def test_script_generation_structure():
    gen = ScriptGenerator()
    research = {
        "topic": "Why Does Bioluminescent Ocean Waves Happen?",
        "category": "Nature & Earth",
        "facts": [
            "Bioluminescence in marine organisms is caused by luciferin chemical reactions.",
            "Single-celled dinoflagellates emit blue light when disturbed by ocean waves.",
            "This light serves as a predator warning and deterrent mechanism."
        ]
    }
    result = gen.generate_script_and_titles(research)
    assert "script_text" in result
    assert "word_count" in result
    assert "hook" in result
    assert "candidate_titles" in result
    assert len(result["candidate_titles"]) >= 3

def test_script_word_count_bounds():
    gen = ScriptGenerator()
    research = {
        "topic": "Bioluminescent Ocean Waves",
        "category": "Nature & Earth",
        "facts": ["Fact 1 text for test.", "Fact 2 text for test."]
    }
    result = gen.generate_script_and_titles(research)
    val = ScriptValidator()
    is_valid, reason = val.validate_script(result)
    assert is_valid, f"Script failed validation: {reason}"
    assert 90 <= result["word_count"] <= 150

def test_script_validator_placeholder_rejection():
    val = ScriptValidator()
    bad_script = {
        "script_text": "Imagine discovering that [INSERT FACT HERE] happened long ago. Historical Subject was very strange. " + "word " * 90,
        "word_count": 95,
        "hook": "Imagine discovering that amazing mystery."
    }
    is_valid, reason = val.validate_script(bad_script)
    assert not is_valid
    assert "placeholder" in reason.lower()

def test_title_validator_generic_rejection():
    val = ScriptValidator()
    topic = "Bioluminescent Ocean Waves"
    titles = [
        "The Legend of Historical Subject",
        "Amazing Mystery Revealed",
        "Why Bioluminescent Ocean Waves Glow Blue"
    ]
    is_valid, selected, reason = val.validate_and_select_title(topic, titles)
    assert is_valid
    assert selected == "Why Bioluminescent Ocean Waves Glow Blue"
