"""Debug: test if _extract_json_block works on the model's actual output."""
import re
import json
import sys
sys.path.insert(0, __import__("pathlib").Path(__file__).resolve().parent.parent)

# Simulate model output
text = '```json\n{\n  "answer": "四位数",\n  "confidence": 0.95\n}\n```'
print("Text:", repr(text))

# Same logic as RealLocalProvider._extract_json_block
match = re.search(r"\{.*\}", text, flags=re.DOTALL)
if match:
    print("Matched:", repr(match.group(0)))
    try:
        payload = json.loads(match.group(0))
        print("Parsed:", payload)
        print("  answer =", repr(payload.get("answer")))
        print("  confidence =", payload.get("confidence"))
    except json.JSONDecodeError as e:
        print("JSON error:", e)
else:
    print("No match!")

# Also test with a non-JSON output
text2 = "1"
match2 = re.search(r"\{.*\}", text2, flags=re.DOTALL)
print("\nFallback text '1':", "match" if match2 else "no match (correct)")

# Test _extract_answer_fallback
import re as _re
text3 = "四位数"
m = _re.search(r"-?\d+", text3)
print(f"Fallback on '{text3}':", m.group(0) if m else "no number found")
