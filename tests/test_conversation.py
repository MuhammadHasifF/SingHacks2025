"""
tests/test_conversation.py
--------------------------
Integration test to verify that the backend can:
1. Load .env variables via backend/config.py
2. Connect to the Groq API using backend/groq/client.py
3. Successfully generate a response using Groq LLM
"""

from backend.groq.client import GroqClient


def test_groq_connection():
    """
    Sends a simple query to Groq and prints the response.
    This confirms end-to-end setup: config → Groq client → API → response.
    """
    print("🔍 Testing Groq SDK connection...")

    # Initialize client
    groq = GroqClient()

    # Example query to test API latency and correctness
    response = groq.ask(
        "Give me one short sentence on why fast language models matter."
    )

    print("✅ Groq responded successfully:\n")
    print(response)


if __name__ == "__main__":
    # Allows direct execution from terminal
    test_groq_connection()
