"""
Test script for the transcription and analysis pipeline
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from transcription.chat_processor import ChatProcessor
from llm.openrouter_tester import OpenRouterTester


def test_chat_processing():
    """Test chat log processing"""
    print("\n" + "="*60)
    print("TESTING CHAT PROCESSING")
    print("="*60)
    
    processor = ChatProcessor()
    
    # Create sample chats
    print("\nCreating sample chat logs...")
    processor.create_sample_chats(num_chats=5)
    
    # Process chats
    print("\nProcessing chat logs...")
    results = processor.batch_process("sample_data/chats")
    
    print(f"\n✓ Successfully processed {len(results)} chat logs")
    return results


def test_llm_analysis():
    """Test LLM analysis"""
    print("\n" + "="*60)
    print("TESTING LLM ANALYSIS")
    print("="*60)
    
    # Check if transcripts exist
    if not os.path.exists("transcription/sample_outputs"):
        print("No transcripts found. Please run chat processing first.")
        return []
    
    tester = OpenRouterTester()
    
    # Analyze transcripts
    print("\nAnalyzing transcripts with LLM...")
    results = tester.batch_analyze("transcription/sample_outputs")
    
    print(f"\n✓ Successfully analyzed {len(results)} transcripts")
    return results


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" CUSTOMER SUPPORT QA - MILESTONE 1 TEST SUITE")
    print("="*70)
    
    try:
        # Test 1: Chat Processing
        chat_results = test_chat_processing()
        
        # Test 2: LLM Analysis
        llm_results = test_llm_analysis()
        
        # Summary
        print("\n" + "="*70)
        print(" TEST SUMMARY")
        print("="*70)
        print(f"\n✓ Chat logs processed: {len(chat_results)}")
        print(f"✓ Transcripts analyzed: {len(llm_results)}")
        print("\n✓ All tests completed successfully!")
        print("\nNext steps:")
        print("1. Add audio files to sample_data/audio/ to test Deepgram")
        print("2. Run: python transcription/deepgram_processor.py")
        print("3. Check outputs in transcription/sample_outputs/")
        print("4. Check analysis in llm/analysis_results/")
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
