"""
backend/groq/client.py
----------------------
Wrapper for the official Groq SDK, providing a clean interface
for chat completions and future model queries.
"""

from groq import Groq
from backend.config import GROQ_API_KEY


class GroqClient:
    """
    A simple Groq API client wrapper used by backend modules.

    Attributes
    ----------
    client : Groq
        Instance of the Groq SDK initialized with your API key.

    Methods
    -------
    ask(prompt: str, model: str = "llama-3.3-70b-versatile", temperature: float = 0.3) -> str
        Sends a prompt to the model and returns its text response.
    """

    def __init__(self, api_key: str = None):
        """Initialize the Groq client with the API key from config or argument."""
        self.client = Groq(api_key=api_key or GROQ_API_KEY)

    def ask(self, prompt: str, model: str = "llama-3.3-70b-versatile", temperature: float = 0.3) -> str:
        """
        Send a prompt to the Groq model and return the generated text.

        Parameters
        ----------
        prompt : str
            The user's input or question.
        model : str, optional
            Model name to use (default is 'llama-3.3-70b-versatile').
        temperature : float, optional
            Degree of randomness in output (0 = deterministic).

        Returns
        -------
        str
            The text output from the Groq model.
        """
        completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=temperature,
        )

        return completion.choices[0].message.content.strip()
