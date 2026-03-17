import re

class ProhibitedScanner:
    """Detects banned language in transcripts using regex."""

    def __init__(self, custom_phrases=None):
        self.banned_phrases = [
            r"that's not my problem",
            r"not my job",
            r"i don't care",
            r"whatever",
            r"shut up",
            r"you're wrong",
            r"stupid",
            r"dumb",
            r"idiot",
            r"terrible service",
            r"don't be ridiculous",
        ]
        if custom_phrases:
            self.banned_phrases.extend(custom_phrases)

        # Add some company-specific ones as requested
        self.company_specific = [
            r"we don't do refunds",
            r"policy says no",
            r"talk to the manager",
            r"can't help you with that",
            r"not our fault",
        ]
        self.banned_phrases.extend(self.company_specific)

        # Compile all patterns
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.banned_phrases]

    def scan(self, transcript_segments):
        """
        Scans transcript segments for prohibited phrases.

        Args:
            transcript_segments: List of dicts with 'text' and 'timestamp'

        Returns:
            List of detected violations with phrase and location.
        """
        violations = []
        for segment in transcript_segments:
            text = segment.get('text', '')
            timestamp = segment.get('start_time', segment.get('timestamp', '0:00'))
            speaker = segment.get('role', segment.get('speaker', 'unknown'))

            # Only scan agent for compliance usually, but can scan both
            if speaker.lower() != 'agent':
                continue

            for pattern in self.patterns:
                match = pattern.search(text)
                if match:
                    violations.append({
                        "phrase": match.group(),
                        "timestamp": timestamp,
                        "text_snippet": text,
                        "speaker": speaker
                    })
        return violations
