import pytest
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'criterion'))

from backend.core.prohibited_scanner import ProhibitedScanner
from backend.core.analyzer import Analyzer

def test_prohibited_scanner():
    scanner = ProhibitedScanner()
    segments = [
        {"role": "agent", "text": "That's not my problem, sorry.", "start_time": 5},
        {"role": "customer", "text": "I don't care about your rules.", "start_time": 10},
        {"role": "agent", "text": "Whatever, just shut up.", "start_time": 15}
    ]
    violations = scanner.scan(segments)

    # Should detect "not my problem", "whatever", "shut up"
    # Note: "i don't care" is in the list but it was spoken by the customer, scanner skips non-agents
    assert len(violations) >= 2
    phrases = [v["phrase"].lower() for v in violations]
    assert "that's not my problem" in phrases
    assert "whatever" in phrases
    assert "shut up" in phrases

def test_analyzer_aggregation():
    # Mock results
    transcript_data = {
        "conversation_id": "test_call",
        "source": "audio",
        "segments": [
            {"role": "agent", "text": "Hello", "start_time": 0, "sentiment_score": 0.5},
            {"role": "customer", "text": "Hi", "start_time": 1, "sentiment_score": 0.1}
        ],
        "full_transcript": "Hello Hi"
    }
    violations = []
    qa_results = {
        "scores": {
            "empathy": 5, "professionalism": 5, "language_quality": 5,
            "resolution": 5, "emotional_intelligence": 5,
            "efficiency": 5, "bias_reduction": 5,
            "overall_compliance": 5
        },
        "reasoning": {k: "Excellent" for k in ["empathy", "professionalism", "language_quality", "resolution", "emotional_intelligence", "efficiency", "bias_reduction", "overall_compliance"]},
        "coaching": []
    }

    analyzer = Analyzer(mock=True)
    result = analyzer._aggregate(transcript_data, violations, qa_results, "Test Agent")

    assert result["overall_score"] == 5.0
    assert result["agent_name"] == "Test Agent"
    assert result["categories"]["communication"] == 5.0

def test_analyzer_compliance_penalty():
    transcript_data = {
        "conversation_id": "fail_call",
        "source": "audio",
        "segments": [],
        "full_transcript": "bad words"
    }
    violations = [{"phrase": "shut up"}]
    qa_results = {
        "scores": {k: 5 for k in ["empathy", "professionalism", "language_quality", "resolution", "emotional_intelligence", "efficiency", "bias_reduction", "overall_compliance"]},
        "reasoning": {k: "Good" for k in ["empathy", "professionalism", "language_quality", "resolution", "emotional_intelligence", "efficiency", "bias_reduction", "overall_compliance"]},
        "coaching": []
    }

    analyzer = Analyzer(mock=True)
    result = analyzer._aggregate(transcript_data, violations, qa_results, "Bad Agent")

    # Compliance should be forced to 1.0 due to violations
    assert result["categories"]["compliance"] == 1.0
    assert result["overall_score"] < 5.0
