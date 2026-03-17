import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class QAEngine:
    """Analyzes transcripts using OpenRouter for scoring and coaching."""

    def __init__(self, api_key=None, mock=False):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.mock = mock
        self.model = "google/gemini-2.0-flash-001"
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def analyze(self, transcript_data):
        """Perform 8-parameter QA scoring and coaching generation."""
        if self.mock or not self.api_key or self.api_key == "your_openrouter_key_here":
            return self._get_mock_analysis()

        prompt = self._build_prompt(transcript_data["full_transcript"])

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": { "type": "json_object" }
            }

            response = requests.post(self.url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            print(f"OpenRouter Error: {e}")
            return self._get_mock_analysis()

    def _build_prompt(self, transcript):
        return f"""
        Analyze the following customer support transcript and provide QA scores (1-5) and coaching tips.

        SCORING RUBRIC:
        1 = Poor (fails basic expectations)
        2 = Below Average (significant gaps)
        3 = Average (meets expectations)
        4 = Good (exceeds expectations)
        5 = Excellent (exemplary)

        TRANSCRIPT:
        {transcript}

        REQUIRED OUTPUT (JSON):
        {{
            "scores": {{
                "empathy": <1-5>,
                "professionalism": <1-5>,
                "language_quality": <1-5>,
                "resolution": <1-5>,
                "emotional_intelligence": <1-5>,
                "efficiency": <1-5>,
                "bias_reduction": <1-5>,
                "overall_compliance": <1-5>
            }},
            "reasoning": {{
                "empathy": "...",
                "professionalism": "...",
                "language_quality": "...",
                "resolution": "...",
                "emotional_intelligence": "...",
                "efficiency": "...",
                "bias_reduction": "...",
                "overall_compliance": "..."
            }},
            "coaching": [
                {{
                    "priority": "High/Medium/Low",
                    "area": "Area Name",
                    "issue": "What went wrong",
                    "transcript_moment": "Quote from transcript",
                    "action": "What to do instead",
                    "impact": "Benefit of change"
                }}
            ]
        }}
        """

    def _get_mock_analysis(self):
        return {
            "scores": {
                "empathy": 2,
                "professionalism": 2,
                "language_quality": 4,
                "resolution": 1,
                "emotional_intelligence": 2,
                "efficiency": 3,
                "bias_reduction": 5,
                "overall_compliance": 1
            },
            "reasoning": {
                "empathy": "Agent dismissed the customer's concern.",
                "professionalism": "Used dismissive language: 'not my problem'.",
                "language_quality": "Grammar was fine but tone was inappropriate.",
                "resolution": "Issue was not resolved.",
                "emotional_intelligence": "Failed to handle customer frustration.",
                "efficiency": "Conversation was short but ineffective.",
                "bias_reduction": "No bias detected.",
                "overall_compliance": "Critical compliance failure due to prohibited phrase."
            },
            "coaching": [
                {
                    "priority": "High",
                    "area": "Empathy",
                    "issue": "Agent used dismissive language: 'that's not my problem'",
                    "transcript_moment": "[0:05] 'That's not my problem though'",
                    "action": "Rephrase to: 'I understand this is frustrating. Let's see how we can resolve this.'",
                    "impact": "Improves customer satisfaction and retention."
                },
                {
                    "priority": "Medium",
                    "area": "Resolution",
                    "issue": "Agent failed to provide any solution or next steps.",
                    "transcript_moment": "End of call",
                    "action": "Always provide a clear next step or reference number.",
                    "impact": "Reduces follow-up calls."
                }
            ]
        }
