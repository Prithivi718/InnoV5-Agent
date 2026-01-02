"""
Semantic Planner (Module 1)

- Calls the LLM
- Produces a STRICT semantic plan JSON
- Does NOT validate feasibility or correctness
"""

import json
import os
from typing import Dict, Union

from dotenv import load_dotenv
from openai import OpenAI

from semantic.prompt import system_prompt, user_prompt
from semantic.question_expander import expand_problem
from semantic.json_utils import extract_json_from_text

load_dotenv()


class SemanticPlannerError(Exception):
    pass


def generate_semantic_plan(problem_text: str) -> Dict[str, Union[str, list, dict]]:
    if not problem_text or not isinstance(problem_text, str):
        raise SemanticPlannerError("Problem text must be a non-empty string")

    detailed_problem = expand_problem(problem_text)

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SemanticPlannerError("OPENROUTER_API_KEY not set")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    try:
        response = client.chat.completions.create(
            # model="qwen/qwen-2.5-7b-instruct",
            # model="deepseek/deepseek-r1-0528:free",
            model="openai/gpt-4o-mini",
            # model="google/gemini-2.0-flash-exp:free",
            messages=[
                {"role": "system", "content": system_prompt()},
                {"role": "user", "content": user_prompt(detailed_problem)}
            ],
            temperature=0
        )
    except Exception as e:
        raise SemanticPlannerError(f"LLM call failed: {e}")

    raw_output = response.choices[0].message.content.strip()

    try:
        parsed = extract_json_from_text(raw_output)
        print(parsed)
    except json.JSONDecodeError:
        raise SemanticPlannerError(
            "LLM did not return valid JSON.\n"
            f"Raw output:\n{raw_output}"
        )

    # Explicit not_expressible passthrough
    if isinstance(parsed, dict) and parsed.get("error") == "not_expressible":
        return parsed

    if not isinstance(parsed, dict):
        raise SemanticPlannerError("Semantic plan must be a JSON object")

    return parsed
