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
    success = "proof completed" in result.stderr.lower() or result.returncode == 0
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
        
        # Append the tactic to the last theorem in the file
        # We assume the last theorem ends with 'by'
        # Correctly append tactic inside a `by` block
        lines = current_code.splitlines()
        for i in reversed(range(len(lines))):
            if lines[i].strip().endswith("by"):
                # Only add tactic if it's not already there
                lines[i] += "\n  " + tactic
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
ftc_code = """theorem add_zero (n : Nat) : n + 0 = n := by
                sorry"""

# Run the prover
prove_lean_code(ftc_code)