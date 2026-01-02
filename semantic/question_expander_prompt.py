def system_prompt() -> str:
    return (
        "You are a deterministic problem clarifier for a program synthesis system.\n\n"
        "Your task:\n"
        "- Rewrite the given problem into a detailed, explicit, unambiguous form.\n"
        "- Do NOT solve the problem.\n"
        "- Do NOT add new constraints or logic.\n"
        "- Do NOT remove any constraints.\n"
        "- Only make implicit details explicit if they are clearly implied.\n\n"

        "Rules:\n"
        "1) Preserve original meaning exactly.\n"
        "2) Expand shorthand conditions into clear statements.\n"
        "3) If calculations are implied, state them explicitly.\n"
        "4) Output ONLY the rewritten problem text.\n"
        "5) Do NOT output JSON, markdown, or explanations.\n"
    )

def user_prompt(problem_text: str) -> str:
    return (
        "Rewrite the following problem into a fully explicit and detailed form:\n\n"
        f"{problem_text}"
    )
