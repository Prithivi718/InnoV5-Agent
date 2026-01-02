import json
from pathlib import Path
from typing import Dict, List


class CapabilityError(Exception):
    pass


class CapabilityValidator:
    def __init__(self, normalized_blocks_path: str):
        self.blocks = self._load_blocks(normalized_blocks_path)
        self.block_types = {b["type"] for b in self.blocks}

    # ---------------------------
    # Load schema
    # ---------------------------
    def _load_blocks(self, path: str) -> List[Dict]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"normalized_blocks.json not found: {path}")

        data = json.loads(p.read_text(encoding='utf-8'))

        if not isinstance(data, list):
            raise TypeError("normalized_blocks.json must be a list")

        for i, block in enumerate(data):
            if "type" not in block:
                raise KeyError(f"Block at index {i} missing 'type'")

        return data

    # ---------------------------
    # Public API
    # ---------------------------
    def validate(self, semantic_plan: Dict) -> Dict:
        try:
            self._validate_inputs(semantic_plan.get("inputs", []))
            self._validate_derived(semantic_plan.get("derived", []))
            self._validate_condition(semantic_plan.get("condition"))
            self._validate_actions(semantic_plan.get("actions", {}))
        except CapabilityError as e:
            return {"status": "error", "reason": str(e)}

        return {"status": "ok"}

    # ---------------------------
    # Helpers
    # ---------------------------
    def _require(self, block_type: str):
        if block_type not in self.block_types:
            raise CapabilityError(f"missing_block: {block_type}")

    # ---------------------------
    # Validators
    # ---------------------------
    def _validate_inputs(self, inputs: List[Dict]):
        if not inputs:
            return

        self._require("variables_set")

        for inp in inputs:
            if "name" not in inp or "type" not in inp:
                raise CapabilityError("invalid_input_schema")

    # -----------------------------
    # Derived (ARITY FIX APPLIED HERE)
    # -----------------------------
    def _validate_derived(self, derived):
        if not derived:
            return

        self._require("variables_set")

        for d in derived:
            expr = d.get("expression")
            if not expr:
                raise CapabilityError("missing_expression")

            op = expr.get("op")
            args = expr.get("args", [])

            # ---------- FIX-1: OPERATOR ARITY VALIDATION ----------
            ARITY = {
                "+": 2,
                "-": 2,
                "*": 2,
                "/": 2,
                "mod": 2,
                "min": 1,
                "max": 1,
                "abs": 1,
                "len": 1,
                "to_string": 1,
                "to_number": 1,
            }

            if op in ARITY:
                if not isinstance(args, list):
                    raise CapabilityError(
                        f"invalid_args: op '{op}' expects list args"
                    )

                expected = ARITY[op]
                if len(args) != expected:
                    raise CapabilityError(
                        f"invalid_arity: op '{op}' expects {expected} args, got {len(args)}"
                    )
            # ------------------------------------------------------


    def _validate_condition(self, condition: Dict):
        if not condition:
            return

        if condition["op"] not in {"and", "or"}:
            raise CapabilityError("unsupported_logic_op")

        self._require("logic_compare")
        self._require("logic_operation")
        self._require("controls_if")

        for c in condition.get("conditions", []):
            if c["op"] not in {">", "<", ">=", "<=", "==", "!="}:
                raise CapabilityError(f"unsupported_comparator: {c['op']}")

    def _validate_actions(self, actions: Dict):
        for branch in ["then", "else"]:
            for action in actions.get(branch, []):
                if action["type"] == "print":
                    self._require("text_print")
                    self._require("text")
                else:
                    raise CapabilityError(f"unsupported_action: {action['type']}")
