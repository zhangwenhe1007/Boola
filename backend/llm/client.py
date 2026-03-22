"""
LLM client for vLLM (OpenAI-compatible API)
"""
from openai import AsyncOpenAI
from typing import Optional
import os


class LLMClient:
    """
    Client for interacting with vLLM server via OpenAI-compatible API.
    """

    SYSTEM_PROMPT = """You are Boola, a helpful Yale assistant. You help students with questions about:
- Courses and academic planning
- Clubs and organizations
- Campus events and activities
- Policies and deadlines
- Research labs and opportunities

RULES:
1. ALWAYS cite sources as [1], [2] with URLs at the end of your response
2. Keep answers concise (under 150 tokens) unless the user asks for detail
3. If information requires login or isn't available, say so and provide relevant links
4. If you're not sure about something, admit it rather than guessing
5. For course/schedule questions, use the provided context carefully

Format your response like this:
[Your answer here with inline citations like [1] and [2]]

Sources:
[1] URL - Title
[2] URL - Title"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "Qwen/Qwen2.5-14B-Instruct",
    ):
        """
        Initialize LLM client.

        Args:
            base_url: vLLM server URL (default: http://localhost:8000/v1)
            api_key: API key (not required for local vLLM)
            model: Model name to use
        """
        self.base_url = base_url or os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
        self.api_key = api_key or os.getenv("VLLM_API_KEY", "not-needed")
        self.model = model

        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    async def generate(
        self,
        query: str,
        context: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a response for the user query.

        Args:
            query: User's question
            context: List of retrieved documents with 'content', 'url', 'title'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated response string
        """
        # Format context for the prompt
        context_str = self._format_context(context)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context_str}\n\nQuestion: {query}",
            },
        ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content

    def _format_context(self, context: list[dict]) -> str:
        """Format retrieved documents for the prompt"""
        if not context:
            return "No relevant context found."

        parts = []
        for i, doc in enumerate(context, 1):
            parts.append(f"[{i}] {doc.get('title', 'Untitled')} ({doc.get('url', '')})")
            parts.append(doc.get("content", "")[:1000])  # Limit context length
            parts.append("")

        return "\n".join(parts)

    async def health_check(self) -> bool:
        """Check if the LLM server is available"""
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False
