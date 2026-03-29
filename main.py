import os
import sys
from dotenv import load_dotenv
from orchestrator_agent import create_orchestrator

# Load environment variables
load_dotenv()

def chat_interface():
    """
    Main entry point for the BanBog Orchestrator Chat.
    """
    # Ensure API Key is present
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n[ERROR] OPENAI_API_KEY not found. Please set it in your environment or .env file.")
        return

    print("\n" + "="*80)
    print("  BANBOG ORCHESTRATOR - CHAT INTERFACE")
    print("  (Type 'exit', 'salir', or 'quit' to end the session)")
    print("="*80 + "\n")

    print("Initializing system... please wait.")
    try:
        orchestrator = create_orchestrator()
        print("System ready! Ask me anything about Products, Reviews, or BRE-B.\n")
    except Exception as e:
        print(f"Failed to initialize orchestrator: {e}")
        return

    while True:
        try:
            # Get user input
            user_input = input("\033[1;34mUSER: \033[0m")
            
            # Exit conditions
            if user_input.lower() in ['exit', 'salir', 'quit', 'q']:
                print("\nExiting chat. Have a great day!")
                break
            
            if not user_input.strip():
                continue

            # Process query
            print("\033[1;32mAGENT:\033[0m Thinking...")
            
            # Using orchestrator.invoke returns the final string response
            answer = orchestrator.invoke(user_input)
            
            print(f"\r\033[1;32mAGENT:\033[0m {answer}\n")
            print("-" * 50)

        except KeyboardInterrupt:
            print("\nExiting chat...")
            break
        except Exception as e:
            print(f"\n[AGENT ERROR] {str(e)}\n")

if __name__ == "__main__":
    chat_interface()
