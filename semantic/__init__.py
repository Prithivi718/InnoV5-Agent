"""
Manual test for Module 1: Semantic Planner

Run this file directly to verify:
- LLM connectivity
- Prompt correctness
- JSON-only output
- Schema-level sanity
"""

from semantic.planner import generate_semantic_plan, SemanticPlannerError


def run_test(problem: str):
    print("\n" + "=" * 60)
    print("PROBLEM:")
    print(problem)
    print("=" * 60)

    try:
        plan = generate_semantic_plan(problem)
        print("SEMANTIC PLAN OUTPUT:\n")
        print(plan)
    except SemanticPlannerError as e:
        print("❌ SemanticPlannerError:")
        print(e)
    except Exception as e:
        print("❌ Unexpected Error:")
        print(e)


if __name__ == "__main__":
    # ------------------------------
    # Test cases
    # ------------------------------

    run_test("Print Hello World")

    run_test(
        "A candidate qualifies only if written score is at least 60 "
        "interview score is at least 15 and total does not exceed 100"
    )

    run_test(
        "Sort a list of numbers and return the median"
    )  # should likely return not_expressible
