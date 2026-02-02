"""
AI-powered reply suggestions using Groq + Llama.
Follows X algorithm insights for maximum engagement.
"""

import os
from pathlib import Path
from loguru import logger
from .config import config

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq not installed. Run: uv add groq")


def load_prompt_template() -> str:
    """Load prompt from external file for easy customization."""
    prompt_path = Path(__file__).parent / "prompt.txt"
    if prompt_path.exists():
        return prompt_path.read_text()
    else:
        logger.warning(f"prompt.txt not found at {prompt_path}, using default")
        return """Generate {num_suggestions} witty reply suggestions for this tweet:
Tweet from @{author}: "{tweet_text}"
Be punchy, max 2 sentences each. Number them 1-{num_suggestions}."""


class AIReplyGenerator:
    """Generate witty, engaging reply suggestions."""
    
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY", "")
        
        if not GROQ_AVAILABLE:
            logger.warning("Groq not installed - AI replies disabled")
            self.client = None
        elif not api_key:
            logger.warning("GROQ_API_KEY not set - AI replies disabled")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
            logger.info("AI Reply Generator initialized")
        
        # Load prompt template
        self.prompt_template = load_prompt_template()
    
    def generate_replies(
        self,
        tweet_text: str,
        author_username: str,
        num_suggestions: int = 5
    ) -> list[str]:
        """
        Generate reply suggestions optimized for X algorithm.
        
        Based on twitter/the-algorithm insights:
        - Replies that spark discussion get distributed
        - Goal: Get the AUTHOR to reply back
        """
        if not self.client:
            return []
        
        # Format prompt with tweet details
        prompt = self.prompt_template.format(
            num_suggestions=num_suggestions,
            author=author_username,
            tweet_text=tweet_text
        )

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You write viral Twitter replies. Short, punchy, get author replies."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=config.groq_model_name,
                temperature=0.9,  # More creative for wit
                max_tokens=500,
            )
            
            response = completion.choices[0].message.content
            
            # Parse numbered replies
            replies = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and len(line) > 2 and line[0].isdigit():
                    # Remove "1. " or "1) " prefix
                    if '. ' in line:
                        reply = line.split('. ', 1)[-1].strip()
                    elif ') ' in line:
                        reply = line.split(') ', 1)[-1].strip()
                    else:
                        reply = line[2:].strip()
                    
                    if reply:
                        replies.append(reply)
            
            logger.debug(f"Generated {len(replies)} reply suggestions")
            return replies[:num_suggestions]
            
        except Exception as e:
            logger.error(f"AI reply generation failed: {e}")
            return []


# Singleton instance
_generator = None


def get_ai_generator() -> AIReplyGenerator:
    """Get or create AI generator singleton."""
    global _generator
    if _generator is None:
        _generator = AIReplyGenerator()
    return _generator


def get_reply_suggestions(tweet_text: str, author: str, num: int = 5) -> list[str]:
    """
    Convenience function for getting reply suggestions.
    
    Args:
        tweet_text: The tweet content
        author: Username of the tweet author
        num: Number of suggestions (default 5)
    
    Returns:
        List of reply suggestions
    """
    generator = get_ai_generator()
    return generator.generate_replies(tweet_text, author, num)


# Test when run directly
if __name__ == "__main__":
    logger.info("Testing AI Reply Generator...")
    logger.info("-" * 40)
    
    test_tweet = "Just announced: AI will replace all jobs by 2030"
    test_author = "techleader"
    
    replies = get_reply_suggestions(test_tweet, test_author)
    
    logger.info(f"Tweet: {test_tweet}")
    logger.info(f"Author: @{test_author}")
    logger.info("\nSuggested Replies:")
    
    for i, reply in enumerate(replies, 1):
        logger.info(f"{i}. {reply}")
