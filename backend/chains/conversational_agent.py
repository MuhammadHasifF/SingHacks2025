"""
LangChain (1.x) conversational agent using Groq + RunnableWithMessageHistory.
Strictly grounded to real insurance data (MSIG TravelEasy, Pre-Ex, Scootsurance).
"""

import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory

# 🧠 Import Hasif Logic Modules
from backend.chains.question_handler import handle_question
from backend.chains.citation_helper import add_citation

load_dotenv()


def create_insurance_agent():
    """
    Travel Insurance Chat Agent:
      ✅ Uses Groq (LangChain)
      ✅ Keeps per-session memory
      ✅ Handles comparison, explanation, eligibility, scenarios
      ✅ Cites real policy sources
      🚫 Never references non-MSISG / Scootsurance products
    """

    # 1️⃣ Initialize Groq LLM
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )

    # 2️⃣ Define a strict prompt
    system_prompt = (
        "You are **Insurance Scammer**, an MSIG x Scootsurance insurance expert. "
        "Your only knowledge sources are the following three policies:\n"
        "- TravelEasy Policy QTD032212\n"
        "- TravelEasy Pre-Ex Policy QTD032212-PX\n"
        "- Scootsurance QSR022206\n\n"
        "❗ You must never mention or recommend other insurance brands or providers. "
        "When comparing or explaining, always base your response strictly on these documents. "
        "If a user asks for a suggestion, describe which of these 3 plans best fits their need. "
        "Be clear, factual, and concise."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    # 3️⃣ Build the LangChain pipeline
    chain = prompt | llm | StrOutputParser()

    # 4️⃣ Memory setup
    store: dict[str, InMemoryChatMessageHistory] = {}

    def _get_history(session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        return store[session_id]

    chat = RunnableWithMessageHistory(
        chain,
        lambda session_id: _get_history(session_id),
        input_messages_key="question",
        history_messages_key="history",
    )

    # 5️⃣ Main function
    def ask(session_id: str, question: str) -> str:
        """
        Handles:
          - Intent routing via Hasif's backend logic
          - LLM phrasing (strictly grounded to JSON)
          - Adds citations
        """
        # Step 1 — Route question through logic
        routed_answer = handle_question(question)

        # Step 2 — Feed both question + routed logic to Groq
        ai_response = chat.invoke(
            {
                "question": (
                    f"User asked: {question}\n"
                    f"Assistant reasoning (from JSON policies): {routed_answer}\n"
                    "Generate a clear response using ONLY these policies. "
                    "If unsure, say 'This information is not specified in the current policy data.'"
                )
            },
            config={"configurable": {"session_id": session_id}},
        )

        # Step 3 — Add clickable citation footer (links to real PDF files)
        return add_citation(ai_response)

    return ask
