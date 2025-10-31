from backend.chains.conversational_agent import create_insurance_agent

def main():
    ask = create_insurance_agent()
    session_id = "local-cli"  # any string; each id keeps its own history

    print("💬 Insurance Scammer (LangChain 1.x + Groq). Ctrl+C to exit.")
    while True:
        try:
            q = input("\n🧑 You: ").strip()
            if not q:
                continue
            a = ask(session_id, q)
            print("\n Insurance Scammer:", a)
        except KeyboardInterrupt:
            print("\n👋 Bye!")
            break

if __name__ == "__main__":
    main()
