"""
OpenRouter LLM Tester
Task 3: Test LLM capabilities with OpenRouter API for quality analysis
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OpenRouterTester:
    """Test LLM analysis using OpenRouter API"""
    
    def __init__(self, api_key=None):
        """Initialize OpenRouter client"""
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY in .env file")
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.available_models = [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4-turbo",
            "meta-llama/llama-3.1-70b-instruct",
            "google/gemini-pro-1.5",
        ]
    
    def analyze_with_llm(self, transcript_text, model="anthropic/claude-3.5-sonnet"):
        """
        Analyze a transcript using OpenRouter LLM
        
        Args:
            transcript_text: The conversation transcript to analyze
            model: The LLM model to use
            
        Returns:
            dict: Analysis results with scores and reasoning
        """
        try:
            print(f"\n{'='*60}")
            print(f"Analyzing with model: {model}")
            print(f"{'='*60}")
            
            # Create analysis prompt
            prompt = f"""Analyze this customer support conversation for quality:

{transcript_text}

Rate the following aspects on a scale of 1-10:
1. Empathy - How well did the agent show understanding and care?
2. Problem Resolution - How effectively was the customer's issue resolved?
3. Professionalism - How professional and courteous was the agent?

Provide your response in the following JSON format:
{{
    "empathy_score": <number 1-10>,
    "empathy_reasoning": "<brief explanation>",
    "resolution_score": <number 1-10>,
    "resolution_reasoning": "<brief explanation>",
    "professionalism_score": <number 1-10>,
    "professionalism_reasoning": "<brief explanation>",
    "overall_quality": "<Excellent/Good/Fair/Poor>"
}}

Respond ONLY with the JSON, no additional text."""
            
            # Call OpenRouter API
            response = self._call_api(prompt, model)
            
            # Parse response
            analysis = self._parse_response(response)
            
            print(f"\n✓ Analysis completed successfully!")
            print(f"  Empathy: {analysis['empathy_score']}/10")
            print(f"  Resolution: {analysis['resolution_score']}/10")
            print(f"  Professionalism: {analysis['professionalism_score']}/10")
            print(f"  Overall: {analysis['overall_quality']}")
            
            return analysis
            
        except Exception as e:
            print(f"\n✗ Error analyzing transcript: {str(e)}")
            raise
    
    def _call_api(self, prompt, model):
        """Make API call to OpenRouter"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        print("Sending request to OpenRouter API...")
        response = requests.post(self.base_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    def _parse_response(self, response):
        """Parse LLM response and extract analysis"""
        try:
            content = response["choices"][0]["message"]["content"]
            
            # Try to extract JSON from response
            # Remove markdown code blocks if present
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            analysis = json.loads(content)
            
            # Validate required fields
            required_fields = [
                "empathy_score", "empathy_reasoning",
                "resolution_score", "resolution_reasoning",
                "professionalism_score", "professionalism_reasoning",
                "overall_quality"
            ]
            
            for field in required_fields:
                if field not in analysis:
                    raise ValueError(f"Missing required field: {field}")
            
            return analysis
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse LLM response as JSON: {str(e)}\nResponse: {content}")
        except Exception as e:
            raise Exception(f"Error parsing response: {str(e)}")
    
    def analyze_transcript_file(self, transcript_file, output_dir="llm/analysis_results", model="anthropic/claude-3.5-sonnet"):
        """
        Analyze a transcript file and save results
        
        Args:
            transcript_file: Path to transcript file (.txt or .json)
            output_dir: Directory to save analysis results
            model: LLM model to use
            
        Returns:
            dict: Complete analysis with metadata
        """
        try:
            print(f"\n{'='*60}")
            print(f"Processing file: {transcript_file}")
            print(f"{'='*60}")
            
            # Read transcript
            transcript_text = self._read_transcript_file(transcript_file)
            
            # Analyze
            analysis = self.analyze_with_llm(transcript_text, model)
            
            # Add metadata
            file_name = Path(transcript_file).stem
            full_analysis = {
                "conversation_id": file_name,
                "analysis": analysis,
                "model_used": model,
                "timestamp": datetime.now().isoformat()
            }
            
            # Save results
            output_path = self._save_analysis(full_analysis, output_dir)
            
            print(f"✓ Saved analysis to: {output_path}")
            
            return full_analysis
            
        except Exception as e:
            print(f"✗ Error processing {transcript_file}: {str(e)}")
            raise
    
    def _read_transcript_file(self, transcript_file):
        """Read and extract text from transcript file"""
        if not os.path.exists(transcript_file):
            raise FileNotFoundError(f"Transcript file not found: {transcript_file}")
        
        file_ext = Path(transcript_file).suffix.lower()
        
        if file_ext == '.json':
            # Read JSON file
            with open(transcript_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract transcript text
            if 'full_transcript' in data:
                return data['full_transcript']
            elif 'messages' in data:
                # Build transcript from messages
                transcript_lines = []
                for msg in data['messages']:
                    speaker = msg.get('speaker', 'unknown').upper()
                    text = msg.get('text', '')
                    transcript_lines.append(f"[{speaker}]: {text}")
                return '\n'.join(transcript_lines)
            else:
                return json.dumps(data)
        
        else:
            # Read text file
            with open(transcript_file, 'r', encoding='utf-8') as f:
                return f.read()
    
    def _save_analysis(self, analysis_data, output_dir):
        """Save analysis results to JSON file"""
        os.makedirs(output_dir, exist_ok=True)
        
        conversation_id = analysis_data["conversation_id"]
        output_file = os.path.join(output_dir, f"analysis_{conversation_id}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2)
        
        return output_file
    
    def compare_models(self, transcript_text, models=None):
        """
        Compare analysis results from different LLM models
        
        Args:
            transcript_text: The conversation transcript
            models: List of models to compare (defaults to available models)
            
        Returns:
            dict: Comparison results from all models
        """
        if models is None:
            models = self.available_models
        
        print(f"\n{'='*60}")
        print(f"Comparing {len(models)} models")
        print(f"{'='*60}")
        
        results = {}
        
        for model in models:
            print(f"\n--- Testing {model} ---")
            try:
                analysis = self.analyze_with_llm(transcript_text, model)
                results[model] = {
                    "success": True,
                    "analysis": analysis
                }
            except Exception as e:
                print(f"✗ Model failed: {str(e)}")
                results[model] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Print comparison summary
        print(f"\n{'='*60}")
        print("MODEL COMPARISON SUMMARY")
        print(f"{'='*60}")
        
        for model, result in results.items():
            print(f"\n{model}:")
            if result["success"]:
                analysis = result["analysis"]
                print(f"  Empathy: {analysis['empathy_score']}/10")
                print(f"  Resolution: {analysis['resolution_score']}/10")
                print(f"  Professionalism: {analysis['professionalism_score']}/10")
                print(f"  Overall: {analysis['overall_quality']}")
            else:
                print(f"  Status: FAILED - {result['error']}")
        
        return results
    
    def batch_analyze(self, transcript_dir, output_dir="llm/analysis_results", model="anthropic/claude-3.5-sonnet"):
        """
        Analyze multiple transcript files
        
        Args:
            transcript_dir: Directory containing transcript files
            output_dir: Directory to save analysis results
            model: LLM model to use
            
        Returns:
            list: List of analysis results
        """
        # Find transcript files
        transcript_files = []
        for ext in ['.txt', '.json']:
            transcript_files.extend(Path(transcript_dir).glob(f'*{ext}'))
        
        if not transcript_files:
            print(f"No transcript files found in {transcript_dir}")
            return []
        
        print(f"\nFound {len(transcript_files)} transcript files to analyze")
        
        results = []
        for i, transcript_file in enumerate(transcript_files, 1):
            print(f"\n[{i}/{len(transcript_files)}] Analyzing {transcript_file.name}...")
            try:
                analysis = self.analyze_transcript_file(str(transcript_file), output_dir, model)
                results.append(analysis)
            except Exception as e:
                print(f"Failed to analyze {transcript_file.name}: {str(e)}")
                continue
        
        print(f"\n{'='*60}")
        print(f"Batch analysis complete!")
        print(f"Successfully analyzed: {len(results)}/{len(transcript_files)} files")
        print(f"{'='*60}\n")
        
        return results


def main():
    """Test the OpenRouter LLM analysis"""
    tester = OpenRouterTester()
    
    # Test with sample transcript
    sample_transcript = """
    [CUSTOMER - 0:00]: Hi, my package hasn't arrived yet.
    [AGENT - 0:05]: I'm sorry to hear that. Let me look into this for you right away.
    [AGENT - 0:10]: Can you provide your order number?
    [CUSTOMER - 0:15]: It's 12345.
    [AGENT - 0:20]: Thank you. I see your order was delayed in transit.
    [AGENT - 0:25]: I'll expedite shipping at no cost to you.
    [CUSTOMER - 0:30]: Thank you so much!
    """
    
    print("Testing with sample transcript...")
    
    try:
        # Test single model
        analysis = tester.analyze_with_llm(sample_transcript)
        print("\nAnalysis Results:")
        print(json.dumps(analysis, indent=2))
        
        # Test model comparison (commented out to save API credits)
        # print("\n\nComparing different models...")
        # comparison = tester.compare_models(sample_transcript, models=tester.available_models[:2])
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Batch analyze if transcripts exist
    transcript_dir = "transcription/sample_outputs"
    if os.path.exists(transcript_dir):
        print(f"\n\nBatch analyzing transcripts from {transcript_dir}...")
        results = tester.batch_analyze(transcript_dir)
        
        if results:
            print("\n" + "="*60)
            print("BATCH ANALYSIS SUMMARY")
            print("="*60)
            for result in results:
                print(f"\n{result['conversation_id']}:")
                analysis = result['analysis']
                print(f"  Empathy: {analysis['empathy_score']}/10")
                print(f"  Resolution: {analysis['resolution_score']}/10")
                print(f"  Professionalism: {analysis['professionalism_score']}/10")
                print(f"  Overall: {analysis['overall_quality']}")


if __name__ == "__main__":
    main()
