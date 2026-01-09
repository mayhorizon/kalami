"""
Conversation service using LLM for language learning
"""
from typing import List, Dict
import openai
from app.core.config import settings


class ConversationService:
    """LLM-powered conversation service for language learning"""

    def __init__(self):
        """Initialize conversation service"""
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def get_system_prompt(self, language: str, level: str = "beginner") -> str:
        """
        Generate system prompt for language learning conversation

        Args:
            language: Target language code
            level: Proficiency level (beginner, intermediate, advanced)

        Returns:
            System prompt
        """
        language_names = {
            "es": "Spanish",
            "fr": "French",
            "de": "German"
        }

        lang_name = language_names.get(language, "the target language")

        return f"""You are a friendly and patient {lang_name} language tutor. Your role is to help the student practice speaking {lang_name} through natural conversation.

Guidelines:
- Respond ONLY in {lang_name}, using vocabulary appropriate for a {level} level student
- Keep your responses conversational and engaging (2-3 sentences max)
- Ask follow-up questions to encourage the student to speak more
- If the student makes a mistake, gently correct it by using the correct form naturally in your response
- Adapt to the student's level - if they struggle, simplify your language
- Be encouraging and supportive
- Focus on practical, everyday conversation topics
- Don't explain grammar unless specifically asked
- Respond as if you're having a real conversation with a friend

Remember: Your goal is to make the student SPEAK as much as possible in {lang_name}."""

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        language: str,
        level: str = "beginner",
        temperature: float = 0.7
    ) -> str:
        """
        Generate conversation response

        Args:
            messages: Conversation history (list of {role, content} dicts)
            language: Target language code
            level: Proficiency level
            temperature: Response randomness (0-2)

        Returns:
            AI response text
        """
        try:
            # Prepare messages with system prompt
            full_messages = [
                {"role": "system", "content": self.get_system_prompt(language, level)}
            ] + messages

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=150  # Keep responses concise for conversation
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise Exception(f"Conversation generation failed: {str(e)}")

    async def analyze_pronunciation(
        self,
        transcribed_text: str,
        expected_text: str = None
    ) -> Dict:
        """
        Analyze pronunciation quality (placeholder)

        Args:
            transcribed_text: What the user actually said
            expected_text: What the user was trying to say (optional)

        Returns:
            Analysis results
        """
        # TODO: Implement proper pronunciation analysis
        # This could use Azure Speech Services or a custom model
        return {
            "accuracy": 0.0,
            "feedback": "Pronunciation analysis not yet implemented",
            "suggestions": []
        }

    async def provide_grammar_feedback(
        self,
        user_text: str,
        language: str
    ) -> Dict:
        """
        Provide grammar feedback on user's input

        Args:
            user_text: User's text in target language
            language: Target language code

        Returns:
            Grammar feedback
        """
        try:
            prompt = f"""Analyze this {language} sentence for grammar errors and provide brief, friendly feedback:
"{user_text}"

Respond in JSON format:
{{
  "has_errors": true/false,
  "corrections": ["list of corrections"],
  "feedback": "brief, encouraging feedback"
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            import json
            return json.loads(response.choices[0].message.content)

        except Exception as e:
            return {
                "has_errors": False,
                "corrections": [],
                "feedback": f"Grammar analysis unavailable: {str(e)}"
            }
