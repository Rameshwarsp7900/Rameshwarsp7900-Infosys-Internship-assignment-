"""
Chat Log Processor
Task 2: Clean and organize chat logs into structured format
"""

import re
import json
from datetime import datetime
from pathlib import Path
import os


class ChatProcessor:
    """Process chat logs into structured format"""
    
    def __init__(self):
        """Initialize chat processor"""
        pass
    
    def process_chat_log(self, chat_file, output_dir="transcription/sample_outputs"):
        """
        Process a chat log file and convert to structured JSON
        
        Args:
            chat_file: Path to the chat log file
            output_dir: Directory to save the structured output
            
        Returns:
            dict: Structured chat data
        """
        try:
            print(f"\n{'='*60}")
            print(f"Processing: {chat_file}")
            print(f"{'='*60}")
            
            # Read chat file
            if not os.path.exists(chat_file):
                raise FileNotFoundError(f"Chat file not found: {chat_file}")
            
            with open(chat_file, 'r', encoding='utf-8') as f:
                chat_text = f.read()
            
            # Parse chat log
            structured_chat = self._parse_chat_log(chat_text, chat_file)
            
            # Save structured output
            output_path = self._save_structured_chat(structured_chat, output_dir)
            
            print(f"\n✓ Chat processing completed successfully!")
            print(f"✓ Saved to: {output_path}")
            print(f"✓ Total messages: {structured_chat['total_messages']}")
            print(f"✓ Agent: {structured_chat.get('agent', 'Unknown')}")
            
            return structured_chat
            
        except Exception as e:
            print(f"\n✗ Error processing {chat_file}: {str(e)}")
            raise
    
    def _parse_chat_log(self, chat_text, chat_file):
        """Parse chat log text into structured format"""
        # Pattern: [timestamp] Speaker: message
        # Supports various formats:
        # [2024-02-13 10:30:00] Customer: message
        # [10:30:00] Agent_Sarah: message
        # [10:30] Customer: message
        
        patterns = [
            # Full datetime with speaker name
            r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s*(.+?):\s*(.+)',
            # Time only with speaker name
            r'\[(\d{2}:\d{2}:\d{2})\]\s*(.+?):\s*(.+)',
            # Short time with speaker name
            r'\[(\d{2}:\d{2})\]\s*(.+?):\s*(.+)',
        ]
        
        messages = []
        lines = chat_text.split('\n')
        
        date = None
        agent_name = None
        
        for line in lines:
            if not line.strip():
                continue
            
            matched = False
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    timestamp, speaker, text = match.groups()
                    
                    # Extract date if present
                    if ' ' in timestamp:
                        date_part, time_part = timestamp.split(' ', 1)
                        if not date:
                            date = date_part
                        timestamp = time_part
                    
                    # Clean speaker name and determine role
                    speaker_clean = speaker.strip()
                    is_agent = any(keyword in speaker_clean.lower() 
                                 for keyword in ['agent', 'support', 'rep', 'representative'])
                    
                    role = "agent" if is_agent else "customer"
                    
                    # Extract agent name if this is an agent message
                    if is_agent and not agent_name:
                        # Try to extract name from speaker field
                        name_match = re.search(r'agent[_\s]*(.+)', speaker_clean, re.IGNORECASE)
                        if name_match:
                            agent_name = name_match.group(1).strip('_- ')
                    
                    messages.append({
                        "timestamp": timestamp,
                        "speaker": role,
                        "speaker_raw": speaker_clean,
                        "text": text.strip()
                    })
                    
                    matched = True
                    break
            
            if not matched and line.strip():
                # Try to append to last message if it's a continuation
                if messages and not line.startswith('['):
                    messages[-1]["text"] += " " + line.strip()
        
        # Generate conversation ID
        file_name = Path(chat_file).stem
        conversation_id = f"chat_{file_name}"
        
        # Calculate duration (time between first and last message)
        duration_seconds = 0
        if len(messages) >= 2:
            try:
                first_time = datetime.strptime(messages[0]["timestamp"], "%H:%M:%S")
                last_time = datetime.strptime(messages[-1]["timestamp"], "%H:%M:%S")
                duration_seconds = (last_time - first_time).seconds
            except:
                try:
                    first_time = datetime.strptime(messages[0]["timestamp"], "%H:%M")
                    last_time = datetime.strptime(messages[-1]["timestamp"], "%H:%M")
                    duration_seconds = (last_time - first_time).seconds
                except:
                    pass
        
        # Structure the data
        structured_chat = {
            "conversation_id": conversation_id,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "duration_seconds": duration_seconds,
            "agent": agent_name or "Unknown",
            "total_messages": len(messages),
            "messages": messages,
            "platform": "web",  # Default, could be detected or set
            "language": "en"
        }
        
        return structured_chat
    
    def _save_structured_chat(self, structured_chat, output_dir):
        """Save structured chat to JSON file"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        conversation_id = structured_chat["conversation_id"]
        output_file = os.path.join(output_dir, f"{conversation_id}.json")
        
        # Save as JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structured_chat, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def batch_process(self, chat_directory, output_dir="transcription/sample_outputs"):
        """
        Process multiple chat log files from a directory
        
        Args:
            chat_directory: Directory containing chat log files
            output_dir: Directory to save structured outputs
            
        Returns:
            list: List of structured chat data for each file
        """
        chat_files = []
        for ext in ['.txt', '.log', '.chat']:
            chat_files.extend(Path(chat_directory).glob(f'*{ext}'))
        
        if not chat_files:
            print(f"No chat files found in {chat_directory}")
            return []
        
        print(f"\nFound {len(chat_files)} chat files to process")
        
        results = []
        for i, chat_file in enumerate(chat_files, 1):
            print(f"\n[{i}/{len(chat_files)}] Processing {chat_file.name}...")
            try:
                structured_chat = self.process_chat_log(str(chat_file), output_dir)
                results.append(structured_chat)
            except Exception as e:
                print(f"Failed to process {chat_file.name}: {str(e)}")
                continue
        
        print(f"\n{'='*60}")
        print(f"Batch processing complete!")
        print(f"Successfully processed: {len(results)}/{len(chat_files)} files")
        print(f"{'='*60}\n")
        
        return results
    
    def create_sample_chats(self, output_dir="sample_data/chats", num_chats=10):
        """
        Create sample chat logs for testing
        
        Args:
            output_dir: Directory to save sample chats
            num_chats: Number of sample chats to create
        """
        os.makedirs(output_dir, exist_ok=True)
        
        scenarios = [
            {
                "type": "order_tracking",
                "messages": [
                    ("[10:30:00]", "Customer", "My order hasn't arrived yet"),
                    ("[10:30:15]", "Agent_Sarah", "I'm sorry to hear that. Let me check your order status."),
                    ("[10:30:45]", "Customer", "Order #12345"),
                    ("[10:31:00]", "Agent_Sarah", "Thank you. I see your order is delayed in transit."),
                    ("[10:31:30]", "Agent_Sarah", "I'll expedite shipping at no cost to you."),
                    ("[10:32:00]", "Customer", "Thank you so much!"),
                ]
            },
            {
                "type": "refund_request",
                "messages": [
                    ("[14:15:00]", "Customer", "I need to request a refund for my recent purchase"),
                    ("[14:15:10]", "Agent_Mike", "I'd be happy to help you with that. Can you tell me more about why you'd like a refund?"),
                    ("[14:15:45]", "Customer", "The product doesn't work as advertised"),
                    ("[14:16:00]", "Agent_Mike", "I understand your frustration. Let me process a full refund for you."),
                    ("[14:16:30]", "Agent_Mike", "Your refund has been initiated and will appear in 3-5 business days."),
                    ("[14:17:00]", "Customer", "Great, thanks for your help"),
                ]
            },
            {
                "type": "technical_issue",
                "messages": [
                    ("[09:00:00]", "Customer", "I can't log into my account"),
                    ("[09:00:20]", "Agent_Lisa", "I'm sorry you're having trouble. Let me help you resolve this."),
                    ("[09:00:35]", "Agent_Lisa", "Have you tried resetting your password?"),
                    ("[09:01:00]", "Customer", "Yes, but I'm not receiving the reset email"),
                    ("[09:01:20]", "Agent_Lisa", "Let me check your account settings."),
                    ("[09:02:00]", "Agent_Lisa", "I've resent the password reset email to your registered address."),
                    ("[09:02:30]", "Customer", "Got it! Thanks!"),
                ]
            },
            {
                "type": "account_problem",
                "messages": [
                    ("[16:45:00]", "Customer", "My account has been charged twice"),
                    ("[16:45:15]", "Agent_Tom", "I apologize for the inconvenience. Let me look into this right away."),
                    ("[16:45:50]", "Agent_Tom", "I can see the duplicate charge. This was an error on our end."),
                    ("[16:46:20]", "Agent_Tom", "I've processed a refund for the duplicate charge."),
                    ("[16:46:45]", "Customer", "When will I see the refund?"),
                    ("[16:47:00]", "Agent_Tom", "It should appear in your account within 2-3 business days."),
                    ("[16:47:20]", "Customer", "Thank you for your help"),
                ]
            },
        ]
        
        for i in range(num_chats):
            scenario = scenarios[i % len(scenarios)]
            filename = f"chat_log_{i+1}_{scenario['type']}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                for timestamp, speaker, text in scenario["messages"]:
                    f.write(f"{timestamp} {speaker}: {text}\n")
            
            print(f"Created: {filename}")
        
        print(f"\n✓ Created {num_chats} sample chat files in {output_dir}")


def main():
    """Test the chat processor with sample files"""
    processor = ChatProcessor()
    
    # Create sample chats if they don't exist
    chat_dir = "sample_data/chats"
    if not os.path.exists(chat_dir) or not os.listdir(chat_dir):
        print("Creating sample chat logs...")
        processor.create_sample_chats(num_chats=10)
    
    # Process all chat files
    if os.path.exists(chat_dir):
        results = processor.batch_process(chat_dir)
        
        if results:
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            for result in results:
                print(f"\n{result['conversation_id']}:")
                print(f"  Date: {result['date']}")
                print(f"  Agent: {result['agent']}")
                print(f"  Messages: {result['total_messages']}")
                print(f"  Duration: {result['duration_seconds']}s")
    else:
        print(f"Chat directory not found: {chat_dir}")


if __name__ == "__main__":
    main()
