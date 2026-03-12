# main_ftc_prover.py
from lmstudio_client import query_llm
import subprocess
from pathlib import Path
import tempfile

# ----------------------------
# Helper functions
# ----------------------------
def write_lean_file(code: str, filename: str = "tmp.lean"):
    file_path = Path(tempfile.gettempdir()) / filename
    file_path.write_text(code)
    return file_path

def lean_check(file_path: Path):
    """Run Lean and return whether proof is complete."""
    result = subprocess.run(
        ["lean", str(file_path)],
        capture_output=True,
        text=True
    )
    # A proof is only complete if Lean exits successfully AND there are no
    # remaining `sorry` placeholders (which exit 0 but leave goals unproven).
    # Lean emits "declaration uses sorry" for any theorem that relies on sorry.
    has_sorry_warning = (
        "declaration uses sorry" in result.stderr.lower()
        or "declaration uses sorry" in result.stdout.lower()
    )
    success = result.returncode == 0 and not has_sorry_warning
    return success, result.stdout, result.stderr

def build_prompt(state_code: str):
    """Build LM Studio prompt for next tactic."""
    return f"""
You are a Lean 4 theorem prover.

Current code:
{state_code}

Provide the next Lean tactic for the last unfinished theorem.
Return only the tactic.
"""

# ----------------------------
# Main prover
# ----------------------------
def prove_lean_code(lean_code: str, max_steps: int = 20):
    file_path = write_lean_file(lean_code)
    
    for step in range(max_steps):
        with open(file_path, "r") as f:
            current_code = f.read()
        
        tactic = query_llm(build_prompt(current_code)).strip()
        print(f"[Step {step+1}] LM Studio tactic suggestion:", tactic)
        
        # Append the tactic after the last existing tactic in the `by` block.
        # We locate the last `sorry` line (the placeholder) and insert the new
        # tactic on a new line directly before it so tactics run in order.
        lines = current_code.splitlines()
        inserted = False
        for i in reversed(range(len(lines))):
            if "sorry" in lines[i]:
                indent = "  "
                lines.insert(i, indent + tactic)
                inserted = True
                break
        if not inserted:
            # No sorry placeholder found – append after the last `by` line.
            for i in reversed(range(len(lines))):
                if lines[i].strip().endswith("by"):
                    lines.insert(i + 1, "  " + tactic)
                    break
        new_code = "\n".join(lines)
        
        file_path.write_text(new_code)
        
        success, stdout, stderr = lean_check(file_path)
        print(stdout)
        print(stderr)
        
        if success:
            print("[INFO] Proof completed!")
            return True
    
    print("[INFO] Proof not finished within max steps")
    return False

# ----------------------------
# Example: Fundamental Theorem of Calculus
# ----------------------------
if __name__ == "__main__":
    ftc_code = "theorem add_zero (n : Nat) : n + 0 = n := by\n  sorry"

    # Run the prover
    prove_lean_code(ftc_code)