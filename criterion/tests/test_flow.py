import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'criterion'))

from backend.core.analyzer import Analyzer
from backend.core.transcription_engine import TranscriptionEngine
from backend.core.qa_engine import QAEngine

def test_transcription_engine_mock():
    engine = TranscriptionEngine(mock=True)
    result = engine.transcribe("dummy.mp3")
    assert result["source"] == "audio"
    assert len(result["segments"]) > 0
    assert "Hello" in result["full_transcript"]

def test_qa_engine_mock():
    engine = QAEngine(mock=True)
    result = engine.analyze({"full_transcript": "test"})
    assert "scores" in result
    assert result["scores"]["empathy"] == 2

def test_analyzer_full_flow_mock():
    analyzer = Analyzer(mock=True)
    # Using a fake file path, it should use mock because mock=True
    result = analyzer.process_file("fake.mp3", agent_name="Agent Smith")
    assert result["agent_name"] == "Agent Smith"
    assert result["overall_score"] > 0
    assert "segments" in result["transcript"][0] or "text" in result["transcript"][0]
