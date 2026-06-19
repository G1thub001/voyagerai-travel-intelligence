from src.tools import run_agent

while True:
    print("\n=== Trip Notes ===")
    print("[10] AI Travel Agent")
    print("[Q] Quit")

    choice = input("\nChoose an option: ").lower()

    if choice == "10":
        question = input("\nAsk the AI Travel Agent: ")

        print("\nThinking...\n")

        answer = run_agent(question)

        print("\nFinal Answer:\n")
        print(answer)

    elif choice == "q":
        print("Goodbye!")
        break

    else:
        print("Invalid option.")