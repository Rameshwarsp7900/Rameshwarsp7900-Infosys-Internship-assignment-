from .transcription_engine import TranscriptionEngine
from .qa_engine import QAEngine
from .prohibited_scanner import ProhibitedScanner
from datetime import datetime

class Analyzer:
    """Aggregates all steps of the QA analysis pipeline."""

    def __init__(self, mock=False):
        self.transcriber = TranscriptionEngine(mock=mock)
        self.qa_engine = QAEngine(mock=mock)
        self.scanner = ProhibitedScanner()

    def process_file(self, file_path, agent_name="Unknown"):
        # 1. Transcribe
        transcript_data = self.transcriber.transcribe(file_path)

        # 2. Scan for prohibited phrases
        violations = self.scanner.scan(transcript_data["segments"])

        # 3. LLM QA Analysis
        qa_results = self.qa_engine.analyze(transcript_data)

        # 4. Aggregate and Calculate Weighted Scores
        analysis = self._aggregate(transcript_data, violations, qa_results, agent_name)

        return analysis

    def _aggregate(self, transcript_data, violations, qa_results, agent_name):
        scores = qa_results["scores"]

        # Calculate Category Scores (Simple Average as requested)
        comm_score = (scores["empathy"] + scores["professionalism"] + scores["language_quality"]) / 3
        prob_score = (scores["resolution"] + scores["emotional_intelligence"]) / 2
        eff_score = (scores["efficiency"] + scores["bias_reduction"]) / 2
        comp_score = scores["overall_compliance"]

        # Apply penalty if prohibited phrases found
        if violations:
            comp_score = min(comp_score, 1.0) # Force compliance to 1 if violations found

        overall_score = (comm_score * 0.25) + (prob_score * 0.25) + (eff_score * 0.15) + (comp_score * 0.35)

        # Determine trend (randomly for demo purposes if no history)
        trend = "stable" # stable, improving, declining

        return {
            "id": transcript_data["conversation_id"],
            "agent_name": agent_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": transcript_data["source"],
            "duration": transcript_data.get("duration", 0),
            "overall_score": round(overall_score, 1),
            "categories": {
                "communication": round(comm_score, 1),
                "problem_solving": round(prob_score, 1),
                "efficiency": round(eff_score, 1),
                "compliance": round(comp_score, 1)
            },
            "parameters": scores,
            "reasoning": qa_results["reasoning"],
            "violations": violations,
            "coaching": qa_results["coaching"],
            "transcript": transcript_data["segments"],
            "full_transcript": transcript_data["full_transcript"],
            "trend": trend,
            "sentiment_timeline": self._build_sentiment_timeline(transcript_data["segments"])
        }

    def _build_sentiment_timeline(self, segments):
        timeline = []
        for seg in segments:
            timeline.append({
                "time": seg.get("start_time", 0),
                "role": seg.get("role"),
                "score": seg.get("sentiment_score", 0),
                "text": seg.get("text")
            })
        return timeline
