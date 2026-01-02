import json
import subprocess
from pathlib import Path
import sys
import plyer

from semantic.planner import generate_semantic_plan, SemanticPlannerError
from semantic.validator import CapabilityValidator
from semantic.compiler import SemanticCompiler
from fallback_llm.llm_xml_generator import generate_fallback_outputs
# from fallback_llm.fallback_writer import write_fallback_outputs

# Import necessary modules

# Gmail 
# from tools.gmail.read_email import read_emails

# -------------------------
# Paths
# -------------------------
ROOT = Path(__file__).parent
OUTPUTS = ROOT / "outputs"

NORMALIZED_BLOCKS = ROOT / "data" / "normalized_blocks.json"
BLOCK_TREE_OUT = ROOT / "semantic" / "output" / "block_tree.json"


# -------------------------
# Helper
# -------------------------
def run_single_test(problem_text: str):
    print("🧪 Running single test mode")

    semantic_plan = generate_semantic_plan(problem_text)
    print(semantic_plan)

    validator = CapabilityValidator(str(NORMALIZED_BLOCKS))
    v = validator.validate(semantic_plan)
    print("Validator:", v)

    if v["status"] != "ok":
        raise RuntimeError("Capability validation failed")

    compiler = SemanticCompiler()
    block_tree = compiler.compile(semantic_plan)

    BLOCK_TREE_OUT.parent.mkdir(parents=True, exist_ok=True)
    BLOCK_TREE_OUT.write_text(json.dumps(block_tree, indent=2))
    print("Wrote block_tree.json")

    run(["node", "generate_xml.js"], cwd=ROOT / "assembler")
    print("XML generated")

    run(["node", "runner_execute.js"], cwd=ROOT / "runner")
    print("Runner completed")

def run_fallback(problem_dir: Path, team_id: str, pid: str, description: str):
    print("⚠️ Running LLM fallback pipeline")

    xml, python_code = generate_fallback_outputs(description)

    xml_dst = problem_dir / f"{team_id}_Mem2_{pid}.xml"
    py_dst = problem_dir / f"{team_id}_Mem2_{pid}.txt"
    bug_dst = problem_dir / f"{team_id}_Mem2_{pid}_bug.txt"

    xml_dst.write_text(xml)
    py_dst.write_text(python_code)
    bug_dst.write_text("Generated via fallback LLM (no validation)\n")

    print(f"🟡 Fallback output written for {pid}")
    show_notification(f"FallBack Completed", f"Fallback output written for {pid}")


# -------------------------
# Helper to run Node scripts
# -------------------------
def run(cmd, cwd):
    subprocess.run(
        cmd,
        cwd=cwd,
        check=True
    )


# -------------------------
# Process one problem
# -------------------------
def process_problem(problem: dict, team_id: str):
    pid = problem["problem_id"]
    description = problem["description"]

    print(f"\n🚀 Processing Problem {pid}")
    show_notification(f"Processing problem {pid}", description)
    print(description)

    problem_dir = OUTPUTS / f"Problem_{pid}"
    problem_dir.mkdir(parents=True, exist_ok=True)

    try:
        # =========================
        # MODULE 1: Semantic Planner
        # =========================
        semantic_plan = generate_semantic_plan(description)

        if semantic_plan.get("error"):
            show_notification(f"Semantic Error", f"{semantic_plan['error']}")
            raise RuntimeError(f"Semantic error: {semantic_plan['error']}")

        show_notification(f"Semantic Plan", "Generated")

        # =========================
        # MODULE 2: Capability Validator
        # =========================
        validator = CapabilityValidator(str(NORMALIZED_BLOCKS))
        validation = validator.validate(semantic_plan)

        if validation["status"] != "ok":
            show_notification(f"Validated Blocks", "compiling...")
            raise RuntimeError(f"Capability error: {validation['reason']}")
        
        show_notification(f"Validated Blocks", "compiling...")

        # =========================
        # MODULE 3: Semantic Compiler
        # =========================
        compiler = SemanticCompiler()
        block_tree = compiler.compile(semantic_plan)

        BLOCK_TREE_OUT.parent.mkdir(parents=True, exist_ok=True)
        BLOCK_TREE_OUT.write_text(json.dumps(block_tree, indent=2))

        show_notification(f"Block Tree", "block-tree.json Generated & written")

        # =========================
        # MODULE 4: XML Generator
        # =========================
        run(
            ["node", "generate_xml.js"],
            cwd=ROOT / "assembler"
        )

        # =========================
        # EXECUTION: CodeAsthram
        # =========================
        run(
            ["node", "runner_execute.js"],
            cwd=ROOT / "runner"
        )

        show_notification(f"Opening CodeAsthram", "executing...")

        # =========================
        # COLLECT OUTPUTS
        # =========================
        xml_src = ROOT / "assembler" / "output" / "program.xml"
        py_src = ROOT / "runner" / "output" / "result.txt"

        xml_dst = problem_dir / f"{team_id}_Mem2_{pid}.xml"
        py_dst = problem_dir / f"{team_id}_Mem2_{pid}.txt"
        bug_dst = problem_dir / f"{team_id}_Mem2_{pid}_bug.txt"

        xml_dst.write_text(xml_src.read_text())
        py_dst.write_text(py_src.read_text())
        bug_dst.write_text("No bugs detected\n")

        print(f"✅ Problem {pid} completed (strict)")
        show_notification(f"{pid} Completed", "Loading next problem...")

    except Exception as e:
        print(f"❌ Strict pipeline failed for {pid}: {e}")
        show_notification(f"Pipeline failed: {pid}", f"{e}")
        run_fallback(problem_dir, team_id, pid, description)

# def process_problem(problem: dict, team_id: str):
#     pid = problem["problem_id"]
#     description = problem["description"]

#     print(f"\n🚀 Processing Problem {pid}")
#     print(description)

#     problem_dir = OUTPUTS / f"Problem_{pid}"
#     problem_dir.mkdir(parents=True, exist_ok=True)

#     run_fallback(problem_dir, team_id, pid, description)


# -------------------------
# Notify the user
# -------------------------
def show_notification(title, message, timeout=10):
    """Displays a cross-platform notification."""
    plyer.notification.notify(
        title=title,
        message=message,
        app_name="InnoGen Agent", # Name of your application
        # app_icon="path/to/icon.ico", # Optional: Path to an .ico file for Windows
        timeout=timeout # Duration in seconds
    )



# -------------------------
# Main entry
# -------------------------
def main():

    # -------- SINGLE TEST MODE --------
    if "--test" in sys.argv:
        problem_text = "Count digits of a Number"
        run_single_test(problem_text)
        return

    # -------- BATCH MODE (unchanged) --------
    problems_path = ROOT / "problems.json"

    if not problems_path.exists():
        print("❌ problems.json not found")
        sys.exit(1)

    with open(problems_path) as f:
        problems = json.load(f)

    team_id = problems.get("team_id", "TEAM_ID0000")
    OUTPUTS.mkdir(exist_ok=True)

    for problem in problems["problems"]:
        process_problem(problem, team_id)


if __name__ == "__main__":
    main()
