from typing import Dict, List, Union


class SemanticCompiler:
    """
    Compiles a semantic plan into a Blockly-aligned block tree.
    """

    # -----------------------------
    # Public API
    # -----------------------------
    def compile(self, plan: Dict) -> Dict:
        head = None
        current = None

        # 1️⃣ Inputs
        for inp in plan.get("inputs", []):
            node = self._compile_input(inp)
            head, current = self._chain(head, current, node)

        # 2️⃣ Derived variables
        for drv in plan.get("derived", []):
            node = self._compile_derived(drv)
            head, current = self._chain(head, current, node)

        # 3️⃣ Condition + actions
        condition = plan.get("condition")
        if condition and condition.get("conditions"):
            node = self._compile_if(condition, plan.get("actions", {}))
            head, current = self._chain(head, current, node)

        return head

    # -----------------------------
    # Helpers
    # -----------------------------
    def _chain(self, head, current, node):
        if head is None:
            return node, node
        current["next"] = node
        return head, node

    # -----------------------------
    # Input
    # -----------------------------
    def _compile_input(self, inp: Dict) -> Dict:
        return {
            "type": "variables_set",
            "fields": {
                "VAR": inp["name"]
            },
            "value_inputs": {
                "VALUE": {
                    "type": "text_prompt_ext",
                    "fields": {
                        "TYPE": "NUMBER" if inp["type"] in {"int", "float"} else "TEXT",
                        "TEXT": ""
                    }
                }
            }
        }

    # -----------------------------
    # Derived
    # -----------------------------
    def _compile_derived(self, drv: Dict) -> Dict:
        return {
            "type": "variables_set",
            "fields": {
                "VAR": drv["name"]
            },
            "value_inputs": {
                "VALUE": self._compile_expression(drv["expression"])
            }
        }

    def _compile_expression(self, expr: Dict) -> Dict:
        op = expr["op"]

        if op in {"+", "-", "*", "/"}:
            return self._compile_arithmetic(expr)

        if op == "abs":
            return {
                "type": "math_single",
                "fields": { "OP": "ABS" },
                "value_inputs": {
                    "NUM": self._compile_value(expr["args"][0])
                }
            }

        if op == "mod":
            return {
                "type": "math_modulo",
                "value_inputs": {
                    "DIVIDEND": self._compile_value(expr["args"][0]),
                    "DIVISOR": self._compile_value(expr["args"][1])
                }
            }

        if op in {"min", "max"}:
            return {
                "type": "math_minmax",
                "fields": { "OP": op.upper() },
                "value_inputs": {
                    "A": self._compile_value(expr["args"][0]),
                    "B": self._compile_value(expr["args"][1])
                }
            }

        if op == "len":
            return {
                "type": "text_length",
                "value_inputs": {
                    "VALUE": self._compile_value(expr["args"][0])
                }
            }

        if op == "to_string":
            return {
                "type": "text_to_string",
                "value_inputs": {
                    "VALUE": self._compile_value(expr["args"][0])
                }
            }

        if op == "to_number":
            return {
                "type": "text_to_number",
                "value_inputs": {
                    "TEXT": self._compile_value(expr["args"][0])
                }
            }

        raise ValueError(f"Unsupported expression op: {op}")


    def _compile_arithmetic(self, expr: Dict) -> Dict:
        op_map = {
            "+": "ADD",
            "-": "MINUS",
            "*": "MULTIPLY",
            "/": "DIVIDE"
        }

        return {
            "type": "math_arithmetic",
            "fields": {
                "OP": op_map[expr["op"]]
            },
            "value_inputs": {
                "A": self._compile_value(expr["args"][0]),
                "B": self._compile_value(expr["args"][1])
            }
        }

    # -----------------------------
    # Condition
    # -----------------------------
    def _compile_if(self, condition: Dict, actions: Dict) -> Dict:
        return {
            "type": "controls_if",
            "value_inputs": {
                "IF0": self._compile_condition(condition)
            },
            "statement_inputs": {
                "DO0": self._compile_actions(actions.get("then", [])),
                "ELSE": self._compile_actions(actions.get("else", []))
            }
        }

    def _compile_condition(self, condition: Dict) -> Dict:
        logic = condition["op"].upper()  # AND / OR
        compiled = [self._compile_compare(c) for c in condition["conditions"]]

        node = compiled[0]
        for next_cond in compiled[1:]:
            node = {
                "type": "logic_operation",
                "fields": {
                    "OP": logic
                },
                "value_inputs": {
                    "A": node,
                    "B": next_cond
                }
            }

        return node

    def _compile_compare(self, c: Dict) -> Dict:
        op_map = {
            "==": "EQ",
            "!=": "NEQ",
            "<": "LT",
            "<=": "LTE",
            ">": "GT",
            ">=": "GTE"
        }

        return {
            "type": "logic_compare",
            "fields": {
                "OP": op_map[c["op"]]
            },
            "value_inputs": {
                "A": self._compile_value(c["left"]),
                "B": self._compile_value(c["right"])
            }
        }

    # -----------------------------
    # Actions
    # -----------------------------
    def _compile_actions(self, actions: List[Dict]) -> Dict:
        head = None
        current = None

        for action in actions:
            if action["type"] == "print":
                node = {
                    "type": "text_print",
                    "value_inputs": {
                        "TEXT": {
                            "type": "text",
                            "fields": {
                                "TEXT": action["value"]
                            }
                        }
                    }
                }
                head, current = self._chain(head, current, node)
            else:
                raise ValueError(f"Unsupported action: {action['type']}")

        return head

    # -----------------------------
    # Values
    # -----------------------------
    def _compile_value(self, v: Union[str, int, float]) -> Dict:
        if isinstance(v, (int, float)):
            return {
                "type": "math_number",
                "fields": {
                    "NUM": str(v)
                }
            }

        return {
            "type": "variables_get",
            "fields": {
                "VAR": v
            }
        }
