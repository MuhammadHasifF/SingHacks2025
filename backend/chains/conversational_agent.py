"""
LangChain (1.x) conversational agent using Groq + RunnableWithMessageHistory.
No LLMChain / ConversationBufferMemory imports needed.
"""

import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory

load_dotenv()


def create_insurance_agent():
    """
    Build a chat agent that:
      - uses Groq via LangChain
      - keeps per-session chat history
      - returns plain text answers
    Returns:
      ask(session_id: str, user_msg: str) -> str
    """

    # 1) LLM
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )

    # 2) Prompt (with history placeholder)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "You are Insurance Scammer, a friendly travel insurance assistant. "
             "Be concise, compare plans when asked, and explain terms clearly."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    # 3) Chain = prompt → llm → text
    chain = prompt | llm | StrOutputParser()

    # 4) Simple in-memory session store
    store: dict[str, InMemoryChatMessageHistory] = {}

    def _get_history(session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        return store[session_id]

    # 5) Wrap chain with chat history support
    chat = RunnableWithMessageHistory(
        chain,
        # how to fetch history per session_id
        lambda session_id: _get_history(session_id),
        input_messages_key="question",
        history_messages_key="history",
    )

    def ask(session_id: str, question: str) -> str:
        """
        Send a message and get a response, remembering per-session context.

        Args:
            session_id: unique id per user/tab/chat
            question: the user's message
        """
        return chat.invoke(
            {"question": question},
            config={"configurable": {"session_id": session_id}},
        )

    return ask
