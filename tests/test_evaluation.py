import sys
import os

# go back one folder > then to src 
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from chain_of_agents import analyse_hn_trends
from datetime import datetime
import json

# this is very manual, placeholder for now, change to using LLM evaluate in the future
def evaluate_answer_quality(query: str, answer: str) -> dict: 

    ''' Metrics for now:
    
    1. length
    2. structure (defined as presence of sections)
    3. time covergae (mentions)
    4. specificity (mentions actual HN articles)
    
    '''

    metrics = {
        "query": query,
        "answer_length": len(answer),
        "has_structure": any(marker in answer.lower() for marker in ["**","1.","-"]),
        "mentions_time_periods": sum(1 for period in ["Q1","Q2","Q3","Q4","2024"] if period in answer),
        "has_specific_data": "discussion" in answer or "story" in answer or "article" in answer,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    score = 0
    if metrics["answer_length"] > 500:
        score += 25
    if metrics["has_structure"]:
        score += 25
    if metrics["mentions_time_periods"] >= 3:
        score += 25
    if metrics["has_specific_data"]:
        score += 25
    
    metrics["overall_score"] = score

    return metrics

def run_evaluation_suite(): 
    
    print("\n" + "="*60)
    print("CHAIN OF AGENTS - EVLAUATION SUITE")
    print("="*60)

    test_cases = [
        {
            "query": "LangChain",
            "expected_themes": ["agents", "chains", "tools", "LLM"],
        },
        {
            "query": "Claude AI",
            "expected_themes": ["Anthropic", "ChatGPT", "comparison"],
        },
    ]
    
    results = []

    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]

        print(f"\n{'='*70}")
        print(f"Test Case {i}/{len(test_cases)}: {query}")
        print(f"{'='*70}")

        try: 
            answer = analyse_hn_trends(query)
            metrics = evaluate_answer_quality(query, answer)    

            print("\n Evaluation results:")
            print(f"- Answer length: {metrics['answer_length']} characters")
            print(f"- Has structure: {metrics['has_structure']}")
            print(f"- Mentions time periods: {metrics['mentions_time_periods']}")
            print(f"- Has specific data: {metrics['has_specific_data']}")
            print(f"- Overall score: {metrics['overall_score']}/100")   

            results.append({
                "test_case": i,
                "query": query,
                "answer": answer,
                "metrics": metrics
            })

        except Exception as e:
            print(f"Error during test case {i}: {str(e)}")
            results.append({
                "test_case": i,
                "query": query,
                "error": str(e)
            })  
        
    # writes eval results into a jason file 
    output_file = "tests/evaluation_results.json"
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*60)
    print(f"\nEvaluation suite completed. Results saved to {output_file}")
    print("="*60)

    avg_score = sum(r.get("metrics", {}).get("overall_score", 0) for r in results) / len(results)
    print("Average Overall Score across test cases: {:.2f}/100".format(avg_score))

    return results

if __name__ == "__main__":
    run_evaluation_suite()






