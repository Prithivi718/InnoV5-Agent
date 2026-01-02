"""
Semantic Planner Output Schema (Module 1)

This schema defines the ONLY structure the LLM
is allowed to output.
"""

# ------------------------------
# Input Variable Schema
# ------------------------------
INPUT_SCHEMA = {
    "name": str,        # variable name
    "type": str         # int | float | string | bool
}

# ------------------------------
# Derived Variable Schema
# ------------------------------
DERIVED_SCHEMA = {
    "name": str,
    "expression": {
        "op": str,      # semantic op (see SEMANTIC_OPS)
        "args": list    # 1 or more arguments
    }
}

# ------------------------------
# Allowed semantic operators
# ------------------------------
SEMANTIC_OPS = {
    # arithmetic
    "+", "-", "*", "/", "mod",

    # unary math
    "abs", "neg", "sqrt",

    # comparisons handled elsewhere
    # string / list
    "len", "to_string", "to_number",

    # min / max
    "min", "max"
}

# ------------------------------
# Atomic Condition Schema
# ------------------------------
CONDITION_ATOM_SCHEMA = {
    "left": object,     # var name or number
    "op": str,          # >= | <= | > | < | == | !=
    "right": object     # var name or number
}

# ------------------------------
# Condition Group Schema
# ------------------------------
CONDITION_SCHEMA = {
    "op": str,              # and | or
    "conditions": list      # list of CONDITION_ATOM_SCHEMA
}

# ------------------------------
# Action Schema
# ------------------------------
ACTION_SCHEMA = {
    "type": str,        # only "print"
    "value": str        # string literal
}

# ------------------------------
# Semantic Plan (FINAL)
# ------------------------------
SEMANTIC_PLAN_SCHEMA = {
    "inputs": list,         # list of INPUT_SCHEMA
    "derived": list,        # list of DERIVED_SCHEMA
    "condition": object,    # CONDITION_SCHEMA or null
    "actions": {
        "then": list,       # list of ACTION_SCHEMA
        "else": list        # list of ACTION_SCHEMA
    }
}
