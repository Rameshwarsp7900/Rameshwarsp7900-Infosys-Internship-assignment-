"""
Main Runner Script
Easily execute all tasks for the Customer Support QA system
"""

import sys
import os
from pathlib import Path


def print_banner(text):
    """Print a formatted banner"""
    width = 70
    print("\n" + "="*width)
    print(f" {text.center(width-2)} ")
    print("="*width + "\n")


def print_menu():
    """Print the main menu"""
    print_banner("CUSTOMER SUPPORT QA - MILESTONE 1")
    print("Choose a task to run:")
    print("\n1. Task 1: Transcribe Audio (Deepgram)")
    print("2. Task 2: Process Chat Logs")
    print("3. Task 3: Analyze with LLM (OpenRouter)")
    print("4. Run All Tasks")
    print("5. Run Tests")
    print("6. Create Sample Data")
    print("7. Exit")
    print("\n" + "="*70)


def task1_transcribe_audio():
    """Run Task 1: Audio Transcription"""
    print_banner("TASK 1: AUDIO TRANSCRIPTION")
    
    # Check if audio files exist
    audio_dir = Path("sample_data/audio")
    if not audio_dir.exists():
        audio_dir.mkdir(parents=True, exist_ok=True)
    
    audio_files = list(audio_dir.glob("*.mp3")) + list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.m4a"))
    
    if not audio_files:
        print("❌ No audio files found in sample_data/audio/")
        print("\nPlease add audio files (mp3, wav, or m4a) to sample_data/audio/")
        print("Then run this task again.")
        return False
    
    # Import and run
    try:
        from transcription.deepgram_processor import DeepgramProcessor
        
        processor = DeepgramProcessor()
        results = processor.batch_transcribe("sample_data/audio")
        
        print(f"\n✅ Successfully transcribed {len(results)} audio files!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if "DEEPGRAM_API_KEY" in str(e):
            print("\nMake sure you have:")
            print("1. Created a .env file (copy from config/.env.example)")
            print("2. Added your Deepgram API key to .env")
        return False


def task2_process_chats():
    """Run Task 2: Chat Processing"""
    print_banner("TASK 2: CHAT LOG PROCESSING")
    
    try:
        from transcription.chat_processor import ChatProcessor
        
        processor = ChatProcessor()
        
        # Check if chat files exist, if not create samples
        chat_dir = Path("sample_data/chats")
        if not chat_dir.exists() or not list(chat_dir.glob("*.txt")):
            print("📝 Creating sample chat logs...")
            processor.create_sample_chats(num_chats=10)
        
        # Process chats
        results = processor.batch_process("sample_data/chats")
        
        print(f"\n✅ Successfully processed {len(results)} chat logs!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def task3_analyze_llm():
    """Run Task 3: LLM Analysis"""
    print_banner("TASK 3: LLM ANALYSIS")
    
    # Check if transcripts exist
    output_dir = Path("transcription/sample_outputs")
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    transcript_files = list(output_dir.glob("*.txt")) + list(output_dir.glob("*.json"))
    
    if not transcript_files:
        print("❌ No transcripts found!")
        print("\nPlease run Task 1 or Task 2 first to generate transcripts.")
        return False
    
    try:
        from llm.openrouter_tester import OpenRouterTester
        
        tester = OpenRouterTester()
        results = tester.batch_analyze("transcription/sample_outputs")
        
        print(f"\n✅ Successfully analyzed {len(results)} transcripts!")
        
        # Print summary
        if results:
            print("\n" + "="*70)
            print("ANALYSIS SUMMARY")
            print("="*70)
            for result in results[:3]:  # Show first 3
                print(f"\n{result['conversation_id']}:")
                analysis = result['analysis']
                print(f"  Empathy: {analysis['empathy_score']}/10")
                print(f"  Resolution: {analysis['resolution_score']}/10")
                print(f"  Professionalism: {analysis['professionalism_score']}/10")
                print(f"  Overall: {analysis['overall_quality']}")
            
            if len(results) > 3:
                print(f"\n... and {len(results) - 3} more")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if "OPENROUTER_API_KEY" in str(e):
            print("\nMake sure you have:")
            print("1. Created a .env file (copy from config/.env.example)")
            print("2. Added your OpenRouter API key to .env")
        return False


def run_all_tasks():
    """Run all three tasks in sequence"""
    print_banner("RUNNING ALL TASKS")
    
    success_count = 0
    
    # Task 2 (Chat processing - no API needed)
    if task2_process_chats():
        success_count += 1
    
    # Task 1 (Audio transcription - needs Deepgram API)
    print("\n")
    if task1_transcribe_audio():
        success_count += 1
    
    # Task 3 (LLM analysis - needs OpenRouter API)
    print("\n")
    if task3_analyze_llm():
        success_count += 1
    
    # Summary
    print("\n" + "="*70)
    print(f"COMPLETED: {success_count}/3 tasks successful")
    print("="*70)


def run_tests():
    """Run the test suite"""
    print_banner("RUNNING TESTS")
    
    try:
        from tests.test_transcription import main as test_main
        test_main()
    except Exception as e:
        print(f"\n❌ Error running tests: {str(e)}")


def create_sample_data():
    """Create sample data"""
    print_banner("CREATING SAMPLE DATA")
    
    try:
        from transcription.chat_processor import ChatProcessor
        
        processor = ChatProcessor()
        processor.create_sample_chats(num_chats=10)
        
        print("\n✅ Sample data created successfully!")
        print("📁 Location: sample_data/chats/")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


def check_setup():
    """Check if the environment is set up correctly"""
    issues = []
    
    # Check for .env file
    if not os.path.exists(".env"):
        issues.append("❌ .env file not found")
        issues.append("   → Copy config/.env.example to .env and add your API keys")
    else:
        # Check if API keys are set
        from dotenv import load_dotenv
        load_dotenv()
        
        if not os.getenv("DEEPGRAM_API_KEY") or os.getenv("DEEPGRAM_API_KEY") == "your_deepgram_key_here":
            issues.append("❌ DEEPGRAM_API_KEY not set in .env")
        else:
            print("✅ Deepgram API key found")
        
        if not os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") == "your_openrouter_key_here":
            issues.append("❌ OPENROUTER_API_KEY not set in .env")
        else:
            print("✅ OpenRouter API key found")
    
    # Check directories
    required_dirs = [
        "sample_data/audio",
        "sample_data/chats",
        "transcription/sample_outputs",
        "llm/analysis_results"
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Required directories created")
    
    if issues:
        print("\n⚠️  Setup Issues Found:")
        for issue in issues:
            print(issue)
        return False
    
    print("\n✅ Environment setup looks good!")
    return True


def main():
    """Main function"""
    # Check setup first
    print_banner("ENVIRONMENT CHECK")
    setup_ok = check_setup()
    
    if not setup_ok:
        print("\n⚠️  Please fix the issues above before continuing.")
        print("Press Enter to continue anyway, or Ctrl+C to exit...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nExiting...")
            return
    
    while True:
        try:
            print_menu()
            choice = input("Enter your choice (1-7): ").strip()
            
            if choice == "1":
                task1_transcribe_audio()
            elif choice == "2":
                task2_process_chats()
            elif choice == "3":
                task3_analyze_llm()
            elif choice == "4":
                run_all_tasks()
            elif choice == "5":
                run_tests()
            elif choice == "6":
                create_sample_data()
            elif choice == "7":
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please enter 1-7.")
            
            print("\n" + "="*70)
            input("Press Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
