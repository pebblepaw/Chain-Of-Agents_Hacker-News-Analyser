import sys
sys.path.append('src')

from chain_of_agents import analyse_hn_trends, visualize_graph
from config import ChainConfig

def main():
    print("\nEnter a topic to analyse, or 'quit' to exit:")
    print("Examples: 'AI agents','LangChain','Claude AI trends'\n")

    while True:
        user_input = input("Your topic: ").strip()
        if user_input.lower() in ['quit', 'exit','q']:
            print("Exiting. Goodbye!")
            break

        print(f"\nAnalyzing Hacker News trends for: {user_input}\n")
        final_answer = analyse_hn_trends(user_input)
        
        print("\n" + "="*60)
        print("FINAL ANALYSIS:")
        print("="*60)
        print(final_answer)
        print("\n" + "="*60 + "\n")

        continue_choice = input("Do you want to analyse another topic? (y/n): ").strip().lower()
        if continue_choice not in ['y', 'yes']:
            print("Exiting. Goodbye!")
            break

    visualize_graph() # generate an image of the graph of agents

if __name__ == '__main__':
    main() 