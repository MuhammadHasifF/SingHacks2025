"""
LangChain (1.x) conversational agent using Groq + RunnableWithMessageHistory.
Strictly grounded to real insurance data (MSIG TravelEasy, Pre-Ex, Scootsurance).
Enhanced for sales-aware behaviour: adapts to user tone, urgency, mindset, and decision stage.
"""

import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 🧠 Import Internal Logic Modules
from backend.chains.question_handler import handle_question
from backend.chains.citation_helper import add_citation

load_dotenv()


def create_insurance_agent():
    """Creates a psychologically adaptive, sales-aware travel insurance chatbot."""

    # 1️⃣  Initialize Groq LLM (LangChain)
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.5,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )

    # 2️⃣  Define AI behaviour and personality
    system_prompt = (
        "You are **MSIG Travel Assistant**, an insurance advisor providing MSIG's travel insurance products. "
        "You only know these policy documents:\n"
        "- TravelEasy Policy QTD032212\n"
        "- TravelEasy Pre-Ex Policy QTD032212-PX\n"
        "- Scootsurance QSR022206\n\n"
        "Be factual and concise, but adapt tone based on the user’s emotional and decision state. "
        "Apply human psychology and ethical sales communication principles to build trust and clarity.\n\n"
        "Tone adaptation rules:\n"
        "• Unsure/Hesitant → Be warm, reassure, ask clarifying questions.\n"
        "• Confused → Simplify terms, use analogies, and confirm understanding.\n"
        "• Angry/Frustrated → Acknowledge emotion, apologise, clarify facts calmly.\n"
        "• Urgent → Give concise next steps first, then context.\n"
        "• Ready to Buy → Be assertive, summarise benefits, reinforce choice confidence.\n"
        "• Exploratory → Be engaging, share interesting plan highlights.\n"
        "• Cautious → Reassure, mention coverage details, mitigate perceived risks.\n\n"
        "Always stay polite, friendly, confident, and empathetic. "
        "End every answer by offering a next helpful step (e.g., 'Would you like to compare plans side by side?')."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    # 3️⃣  Chain construction (LLM + output parser)
    chain = prompt | llm | StrOutputParser()

    # 4️⃣  Conversation memory
    store: dict[str, InMemoryChatMessageHistory] = {}

    def _get_history(session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        return store[session_id]

    chat = RunnableWithMessageHistory(
        chain.with_config(run_name="chat"),
        get_session_history=_get_history,
        input_messages_key="question",
        history_messages_key="history",
    )

    # 5️⃣  Main conversational method
    def ask(session_id: str, question: str) -> str:
        """
        Handles:
          - Intent routing via Hasif’s backend logic
          - Behaviour-aware tone detection
          - LLM phrasing grounded to real JSON data
          - Adds citations to PDFs
        """

        routed_answer = handle_question(question)
        q_lower = question.lower()

        # Behaviour/tone classification
        if any(
            k in q_lower
            for k in ["not sure", "don’t know", "maybe", "which", "help me decide"]
        ):
            user_state = "unsure"
        elif any(k in q_lower for k in ["confused", "don’t understand", "complicated"]):
            user_state = "confused"
        elif any(
            k in q_lower for k in ["angry", "frustrated", "unfair", "why", "hate"]
        ):
            user_state = "frustrated"
        elif any(
            k in q_lower for k in ["quick", "asap", "urgent", "flight soon", "leaving"]
        ):
            user_state = "urgent"
        elif any(k in q_lower for k in ["ready", "buy", "decide", "i’ll choose"]):
            user_state = "ready"
        elif any(k in q_lower for k in ["what if", "explore", "browsing", "curious"]):
            user_state = "exploratory"
        elif any(
            k in q_lower for k in ["worried", "concerned", "risk", "pre-existing"]
        ):
            user_state = "cautious"
        else:
            user_state = "neutral"

        # Query Groq conversationally
        ai_response = chat.invoke(
            {
                "question": (
                    f"User said: {question}\n"
                    f"Detected user mindset: {user_state}\n"
                    f"Assistant reasoning (from JSON policies): {routed_answer}\n"
                    "Now respond naturally, applying psychological sales communication, "
                    "while staying strictly factual and grounded to MSIG/Scootsurance data."
                )
            },
            config={"configurable": {"session_id": session_id}},
        )

        # Add clickable citations
        return add_citation(ai_response)

    return ask
