"""
FREE Conversation service using Ollama + Llama 3 (local LLM)
Zero API costs - runs completely locally
"""
from typing import List, Dict
import ollama


class OllamaConversationService:
    """
    FREE LLM-powered conversation using Ollama

    Recommended models (all FREE):
    - llama3.2:1b - Fastest, ~1GB RAM, good for testing
    - llama3.2:3b - Good balance, ~3GB RAM
    - llama3.2 (8b) - Best quality, ~8GB RAM
    - mistral - Alternative, ~4GB RAM
    """

    def __init__(self, model: str = "llama3.2:3b"):
        """
        Initialize Ollama conversation service

        Args:
            model: Model name (llama3.2:1b, llama3.2:3b, llama3.2, mistral, etc.)

        Installation:
            1. Install Ollama: https://ollama.com/
            2. Pull model: ollama pull llama3.2:3b
            3. Start Ollama server: ollama serve
        """
        self.model = model
        self._check_ollama_available()

    def _check_ollama_available(self):
        """Check if Ollama is running and model is available"""
        try:
            # Check if Ollama server is running
            models = ollama.list()
            print(f"✓ Ollama connected. Available models: {len(models.get('models', []))}")

            # Check if our model is downloaded
            model_names = [m['name'] for m in models.get('models', [])]
            if not any(self.model in name for name in model_names):
                print(f"⚠ Model '{self.model}' not found. Downloading...")
                print(f"Run: ollama pull {self.model}")
                print("This will download ~1-3GB depending on model size")

        except Exception as e:
            raise Exception(
                f"Ollama not available: {str(e)}\n"
                "Install Ollama from: https://ollama.com/\n"
                "Then run: ollama serve"
            )

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
- Keep your responses very short and conversational (1-2 sentences max)
- Ask follow-up questions to encourage the student to speak more
- If the student makes a mistake, gently correct it by using the correct form naturally in your response
- Adapt to the student's level - if they struggle, simplify your language
- Be encouraging and supportive
- Focus on practical, everyday conversation topics
- Don't explain grammar unless specifically asked
- Respond as if you're having a real conversation with a friend

Remember: Your goal is to make the student SPEAK as much as possible in {lang_name}. Keep responses brief to encourage student participation."""

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        language: str,
        level: str = "beginner",
        temperature: float = 0.7
    ) -> str:
        """
        Generate conversation response using Ollama

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

            # Call Ollama API
            response = ollama.chat(
                model=self.model,
                messages=full_messages,
                options={
                    "temperature": temperature,
                    "num_predict": 100,  # Limit response length (keep it conversational)
                }
            )

            return response['message']['content'].strip()

        except Exception as e:
            raise Exception(f"Ollama conversation generation failed: {str(e)}")

    async def generate_streaming_response(
        self,
        messages: List[Dict[str, str]],
        language: str,
        level: str = "beginner"
    ):
        """
        Generate streaming response for real-time conversation

        Args:
            messages: Conversation history
            language: Target language code
            level: Proficiency level

        Yields:
            Response chunks
        """
        try:
            full_messages = [
                {"role": "system", "content": self.get_system_prompt(language, level)}
            ] + messages

            # Stream response from Ollama
            stream = ollama.chat(
                model=self.model,
                messages=full_messages,
                stream=True,
                options={"temperature": 0.7, "num_predict": 100}
            )

            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']

        except Exception as e:
            raise Exception(f"Ollama streaming failed: {str(e)}")

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
            language_names = {"es": "Spanish", "fr": "French", "de": "German"}
            lang_name = language_names.get(language, "the target language")

            prompt = f"""Analyze this {lang_name} sentence for grammar errors and provide brief, friendly feedback:
"{user_text}"

Respond in this exact JSON format:
{{
  "has_errors": true or false,
  "corrections": ["list of corrections if any"],
  "feedback": "brief, encouraging feedback in English"
}}

If there are no errors, just say the sentence is correct."""

            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json"  # Request JSON format
            )

            import json
            return json.loads(response['message']['content'])

        except Exception as e:
            return {
                "has_errors": False,
                "corrections": [],
                "feedback": f"Grammar analysis unavailable: {str(e)}"
            }

    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        try:
            info = ollama.show(self.model)
            return {
                "model": self.model,
                "parameters": info.get('details', {}).get('parameter_size', 'unknown'),
                "family": info.get('details', {}).get('family', 'unknown'),
                "format": info.get('details', {}).get('format', 'unknown')
            }
        except Exception as e:
            return {"error": str(e)}


# Installation and usage instructions:
"""
OLLAMA SETUP:

1. Install Ollama:
   - macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh
   - Windows: Download from https://ollama.com/download

2. Start Ollama server:
   ollama serve

3. Download a model (choose one based on your RAM):
   ollama pull llama3.2:1b    # Fastest, ~1GB RAM
   ollama pull llama3.2:3b    # Recommended, ~3GB RAM
   ollama pull llama3.2       # Best quality, ~8GB RAM
   ollama pull mistral        # Alternative, ~4GB RAM

4. Test it:
   ollama run llama3.2:3b "Hello, how are you?"

5. The Ollama server runs on: http://localhost:11434

HARDWARE REQUIREMENTS:
- llama3.2:1b -> 2GB RAM minimum
- llama3.2:3b -> 6GB RAM minimum
- llama3.2 (8b) -> 16GB RAM minimum

All models work on CPU (no GPU required), though GPU is faster.
"""
