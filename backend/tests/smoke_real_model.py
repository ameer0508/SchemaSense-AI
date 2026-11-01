"""Script to execute live smoke test against Qwen2.5-Coder-1.5B-Instruct."""

import json
import time
import urllib.request

questions = [
    "Show the top 5 students with the highest GPA",
    "How many courses are currently offered in the university?",
    "List all students alongside their department name",
]

print("================================================================")
print("  SchemaSense AI — Phase 4 Real Model Live Inference Smoke Test ")
print("  Model: Qwen/Qwen2.5-Coder-1.5B-Instruct (CPU Inference)")
print("================================================================")

for i, q in enumerate(questions, 1):
    print(f"\n[Test {i}/3] Question: '{q}'")
    payload = json.dumps({
        "question": q,
        "database_id": "campus_intelligence",
        "temperature": 0.0,
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://127.0.0.1:8001/api/ai/generate-sql",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            resp = json.loads(response.read().decode("utf-8"))
            elapsed = time.time() - t0

            print(f"  -> Generated SQL: {resp['sql']}")
            print(f"  -> Validation: {resp['validation']['status']} (Valid: {resp['validation']['is_valid']})")
            print(f"  -> AST Type: {resp['validation']['ast_type']}")
            print(f"  -> Tables Referenced: {resp['validation']['tables_referenced']}")
            print(f"  -> Columns Referenced: {resp['validation']['columns_referenced']}")
            print(f"  -> Validation Issues: {resp['validation']['issues']}")
            print(f"  -> Explanation: {resp.get('explanation')}")
            print(f"  -> Assumptions: {resp.get('assumptions')}")
            print(f"  -> Generation Time: {resp['generation_time_ms']} ms (Total roundtrip: {round(elapsed*1000, 2)} ms)")
    except Exception as e:
        print(f"  -> Error executing query {i}: {e}")

print("\nSmoke test complete.")
