import requests

URL = "http://127.0.0.1:1234/v1/chat/completions"

def query_llm(prompt):

    response = requests.post(
        URL,
        json={
            "model": "local-model",
            "messages": [
                {"role": "system", "content": "You are an expert Lean 4 theorem prover."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 200
        }
    )

    return response.json()["choices"][0]["message"]["content"]


def build_prompt(goal):

    return f"""
You are a Lean 4 theorem prover.

Goal:
{goal}

Provide the next Lean tactic.

Return only the tactic.
"""

def run_tactic(env, tactic):

    try:
        new_state = env.step(tactic)
        return new_state, True
    except:
        return None, False