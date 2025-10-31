"""
LangChain (1.x) conversational agent using Groq + RunnableWithMessageHistory.
Integrated with Hasif's logic modules for:
 - Policy comparison
 - Explanation
 - Eligibility
 - Scenario analysis
 - Citations
"""

import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory

# Import Hasif Logic Modules 🧠
from backend.chains.question_handler import handle_question
from backend.chains.citation_helper import add_citations

load_dotenv()


def create_insurance_agent():
    """
    Build a chat agent that:
      ✅ Uses Groq (via LangChain)
      ✅ Keeps per-session chat history
      ✅ Routes user intent (comparison, explanation, eligibility, scenario)
      ✅ Adds policy citations
    Returns:
      ask(session_id: str, user_msg: str) -> str
    """

    # 1️⃣ Initialize Groq LLM
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )

    # 2️⃣ Define prompt template (with memory placeholder)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "You are JazzBot, a friendly, accurate travel insurance assistant. "
             "Use real policy logic when available, be concise, and always provide factual, cited answers."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    # 3️⃣ Chain together the prompt → LLM → output parser
    chain = prompt | llm | StrOutputParser()

    # 4️⃣ In-memory chat store per user/session
    store: dict[str, InMemoryChatMessageHistory] = {}

    def _get_history(session_id: str) -> InMemoryChatMessageHistory:
        """Retrieve or create chat history per user session."""
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        return store[session_id]

    # 5️⃣ Wrap with message history (LangChain 1.x pattern)
    chat = RunnableWithMessageHistory(
        chain,
        lambda session_id: _get_history(session_id),
        input_messages_key="question",
        history_messages_key="history",
    )

    # 6️⃣ Define sample structured data for comparisons
    policies = {
        "A": {"medical_coverage": 100000, "trip_cancellation": 5000},
        "B": {"medical_coverage": 75000, "trip_cancellation": 2000},
    }

    # 7️⃣ Core function
    def ask(session_id: str, question: str) -> str:
        """
        Process a user question, applying logic + memory + citations.
        """

        # Step 1: Hasif logic (intent-based reasoning)
        routed_answer = handle_question(question, policies)

        # Step 2: Ask the Groq model, with routed logic as context
        ai_response = chat.invoke(
            {
                "question": (
                    f"User asked: {question}\n"
                    f"Assistant reasoning: {routed_answer}\n"
                    "Please summarize or expand this as a helpful insurance assistant."
                )
            },
            config={"configurable": {"session_id": session_id}},
        )

        # Step 3: Attach citations
        final_response = add_citations(
            ai_response,
            [{"text": "Policy Wordings Section 4.2 - Medical Benefits", "source": "MSIG_TravelPlus.pdf"}],
        )

        return final_response

    return ask
