import unittest
from unittest.mock import patch, MagicMock
import os

from x_monitor_bot.ai_replies import get_reply_suggestions, AIReplyGenerator

class TestAIReplyGenerator(unittest.TestCase):

    @patch('x_monitor_bot.ai_replies._generator', new=None)
    @patch.dict(os.environ, {}, clear=True)
    def test_no_groq_api_key(self):
        """Test that AI replies are disabled if GROQ_API_KEY is not set."""
        generator = AIReplyGenerator()
        self.assertIsNone(generator.client)
        replies = get_reply_suggestions("test tweet", "test_author")
        self.assertEqual(replies, [])

    @patch('x_monitor_bot.ai_replies._generator', new=None)
    @patch('x_monitor_bot.ai_replies.GROQ_AVAILABLE', False)
    def test_groq_not_installed(self):
        """Test that AI replies are disabled if groq is not installed."""
        generator = AIReplyGenerator()
        self.assertIsNone(generator.client)
        replies = get_reply_suggestions("test tweet", "test_author")
        self.assertEqual(replies, [])

    @patch('x_monitor_bot.ai_replies._generator', new=None)
    @patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"})
    @patch('x_monitor_bot.ai_replies.Groq')
    def test_generate_replies_success(self, mock_groq):
        """Test successful generation of replies."""
        mock_completion = MagicMock()
        # Replies need to be > 10 chars to pass parser minimum length check
        mock_completion.choices[0].message.content = "1. This is a witty reply that would work great\n2. Another clever response to engage the author\n3. A third punchy comeback for variety"
        mock_groq.return_value.chat.completions.create.return_value = mock_completion

        replies = get_reply_suggestions("test tweet", "test_author", num=3)
        self.assertEqual(len(replies), 3)
        self.assertEqual(replies[0], "This is a witty reply that would work great")
        self.assertEqual(replies[1], "Another clever response to engage the author")
        self.assertEqual(replies[2], "A third punchy comeback for variety")

    @patch('x_monitor_bot.ai_replies._generator', new=None)
    @patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"})
    @patch('x_monitor_bot.ai_replies.Groq')
    def test_generate_replies_empty_response(self, mock_groq):
        """Test handling of an empty response from the API."""
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = ""
        mock_groq.return_value.chat.completions.create.return_value = mock_completion

        replies = get_reply_suggestions("test tweet", "test_author")
        self.assertEqual(replies, [])

    @patch('x_monitor_bot.ai_replies._generator', new=None)
    @patch.dict(os.environ, {"GROQ_API_KEY": "fake_key"})
    @patch('x_monitor_bot.ai_replies.Groq')
    def test_generate_replies_malformed_response(self, mock_groq):
        """Test handling of a malformed response from the API."""
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "This is not a numbered list"
        mock_groq.return_value.chat.completions.create.return_value = mock_completion

        replies = get_reply_suggestions("test tweet", "test_author")
        self.assertEqual(replies, [])


if __name__ == '__main__':
    unittest.main()
