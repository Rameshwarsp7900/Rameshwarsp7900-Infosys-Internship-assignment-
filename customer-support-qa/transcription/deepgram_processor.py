"""
Deepgram Audio Transcription Processor
Task 1: Convert customer support call recordings to text
"""

from deepgram import DeepgramClient, PrerecordedOptions, FileSource
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DeepgramProcessor:
    """Process audio files using Deepgram API"""
    
    def __init__(self, api_key=None):
        """Initialize Deepgram client"""
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("Deepgram API key not found. Set DEEPGRAM_API_KEY in .env file")
        self.client = DeepgramClient(self.api_key)
    
    def transcribe_audio(self, audio_file_path, output_dir="transcription/sample_outputs"):
        """
        Transcribe an audio file using Deepgram API
        
        Args:
            audio_file_path: Path to the audio file
            output_dir: Directory to save the transcript
            
        Returns:
            dict: Transcript data with metadata
        """
        try:
            print(f"\n{'='*60}")
            print(f"Processing: {audio_file_path}")
            print(f"{'='*60}")
            
            # Check if file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Determine file format
            file_ext = Path(audio_file_path).suffix.lower()
            mime_types = {
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.m4a': 'audio/mp4',
                '.mp4': 'audio/mp4',
                '.ogg': 'audio/ogg',
                '.flac': 'audio/flac'
            }
            mimetype = mime_types.get(file_ext, 'audio/mpeg')
            
            # Read audio file
            with open(audio_file_path, "rb") as audio:
                buffer_data = audio.read()
            
            payload: FileSource = {
                "buffer": buffer_data,
            }
            
            # Configure transcription options
            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                diarize=True,  # Enable speaker detection
                punctuate=True,
                paragraphs=True,
                utterances=True,
                language="en"
            )
            
            # Transcribe
            print("Sending to Deepgram API...")
            response = self.client.listen.rest.v("1").transcribe_file(
                payload, options
            )
            
            # Extract results
            results = response.to_dict()
            
            # Process transcript
            transcript_data = self._process_transcript(results, audio_file_path)
            
            # Save transcript
            output_path = self._save_transcript(transcript_data, output_dir)
            
            print(f"\n✓ Transcription completed successfully!")
            print(f"✓ Saved to: {output_path}")
            print(f"✓ Duration: {transcript_data['duration_seconds']} seconds")
            print(f"✓ Speakers detected: {len(transcript_data['speakers'])}")
            
            return transcript_data
            
        except Exception as e:
            print(f"\n✗ Error transcribing {audio_file_path}: {str(e)}")
            raise
    
    def _process_transcript(self, results, audio_file_path):
        """Process raw Deepgram response into structured format"""
        try:
            channel = results["results"]["channels"][0]
            alternatives = channel["alternatives"][0]
            
            # Extract full transcript
            full_transcript = alternatives.get("transcript", "")
            
            # Extract metadata
            metadata = results.get("metadata", {})
            duration = metadata.get("duration", 0)
            
            # Process speakers and segments
            speakers = []
            segments = []
            
            # Get utterances (speaker-separated segments)
            utterances = alternatives.get("utterances", [])
            
            if utterances:
                for utterance in utterances:
                    speaker_id = utterance.get("speaker", 0)
                    
                    # Determine role (assume first speaker is agent)
                    role = "agent" if speaker_id == 0 else "customer"
                    
                    segment = {
                        "start_time": round(utterance.get("start", 0), 2),
                        "end_time": round(utterance.get("end", 0), 2),
                        "speaker_id": speaker_id,
                        "role": role,
                        "text": utterance.get("transcript", "")
                    }
                    segments.append(segment)
                    
                    # Track unique speakers
                    if speaker_id not in [s["speaker_id"] for s in speakers]:
                        speakers.append({
                            "speaker_id": speaker_id,
                            "role": role
                        })
            else:
                # Fallback if no utterances available
                words = alternatives.get("words", [])
                if words:
                    for word in words:
                        speaker_id = word.get("speaker", 0)
                        role = "agent" if speaker_id == 0 else "customer"
                        
                        if speaker_id not in [s["speaker_id"] for s in speakers]:
                            speakers.append({
                                "speaker_id": speaker_id,
                                "role": role
                            })
            
            # Create structured transcript
            file_name = Path(audio_file_path).stem
            transcript_data = {
                "conversation_id": f"call_{file_name}",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "duration_seconds": round(duration, 2),
                "agent_name": "Unknown",  # Would need to be set externally
                "speakers": speakers,
                "segments": segments,
                "full_transcript": full_transcript,
                "audio_quality": "good",  # Could be enhanced with quality detection
                "language": "en",
                "source_file": audio_file_path
            }
            
            return transcript_data
            
        except Exception as e:
            raise Exception(f"Error processing transcript: {str(e)}")
    
    def _save_transcript(self, transcript_data, output_dir):
        """Save transcript to text file"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        conversation_id = transcript_data["conversation_id"]
        output_file = os.path.join(output_dir, f"{conversation_id}.txt")
        
        # Format transcript for text file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Conversation ID: {transcript_data['conversation_id']}\n")
            f.write(f"Date: {transcript_data['date']}\n")
            f.write(f"Duration: {transcript_data['duration_seconds']} seconds\n")
            f.write(f"Agent: {transcript_data['agent_name']}\n")
            f.write(f"\n{'='*60}\n\n")
            
            # Write segments with speaker labels
            for segment in transcript_data["segments"]:
                timestamp = f"{segment['start_time']:.1f}"
                speaker = segment['role'].upper()
                text = segment['text']
                f.write(f"[{speaker} - {timestamp}s]: {text}\n")
            
            f.write(f"\n{'='*60}\n")
            f.write(f"\nFull Transcript:\n{transcript_data['full_transcript']}\n")
        
        # Also save as JSON
        json_file = os.path.join(output_dir, f"{conversation_id}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2)
        
        return output_file
    
    def batch_transcribe(self, audio_directory, output_dir="transcription/sample_outputs"):
        """
        Transcribe multiple audio files from a directory
        
        Args:
            audio_directory: Directory containing audio files
            output_dir: Directory to save transcripts
            
        Returns:
            list: List of transcript data for each file
        """
        audio_files = []
        for ext in ['.mp3', '.wav', '.m4a', '.mp4']:
            audio_files.extend(Path(audio_directory).glob(f'*{ext}'))
        
        if not audio_files:
            print(f"No audio files found in {audio_directory}")
            return []
        
        print(f"\nFound {len(audio_files)} audio files to process")
        
        results = []
        for i, audio_file in enumerate(audio_files, 1):
            print(f"\n[{i}/{len(audio_files)}] Processing {audio_file.name}...")
            try:
                transcript = self.transcribe_audio(str(audio_file), output_dir)
                results.append(transcript)
            except Exception as e:
                print(f"Failed to process {audio_file.name}: {str(e)}")
                continue
        
        print(f"\n{'='*60}")
        print(f"Batch processing complete!")
        print(f"Successfully processed: {len(results)}/{len(audio_files)} files")
        print(f"{'='*60}\n")
        
        return results


def main():
    """Test the transcription with sample audio files"""
    # Initialize processor
    processor = DeepgramProcessor()
    
    # Test with sample audio directory
    audio_dir = "sample_data/audio"
    
    if os.path.exists(audio_dir):
        # Batch process all audio files
        results = processor.batch_transcribe(audio_dir)
        
        if results:
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            for result in results:
                print(f"\n{result['conversation_id']}:")
                print(f"  Duration: {result['duration_seconds']}s")
                print(f"  Speakers: {len(result['speakers'])}")
                print(f"  Segments: {len(result['segments'])}")
    else:
        print(f"Audio directory not found: {audio_dir}")
        print("Please add audio files to sample_data/audio/ directory")


if __name__ == "__main__":
    main()
