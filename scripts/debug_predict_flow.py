"""Debug the RealLocalProvider.predict flow step by step."""
import re
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.llm_provider import RealLocalProvider
from src.models import Mode, StageConfig

provider = RealLocalProvider("Qwen/Qwen2.5-0.5B-Instruct")
stage = StageConfig(1, "DigitCounting", False, None, False, False)
mode = Mode.EXPERT

# Manually do what predict does
provider._ensure_loaded()
system_prompt = "Return JSON only with keys: answer (string), confidence (number 0 to 1)."
question = "数字 2 一共有几位？"
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": f"Question: {question}"},
]

text = provider._tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
print("=== FULL PROMPT ===")
print(text)
print()

inputs = provider._tokenizer(text, return_tensors="pt").to(provider._model.device)
print(f"Input shape: {inputs['input_ids'].shape}")
print(f"Input length: {inputs['input_ids'].shape[1]} tokens")

outputs = provider._model.generate(
    **inputs,
    max_new_tokens=64,
    temperature=0.0,
    do_sample=False,
    pad_token_id=provider._tokenizer.pad_token_id,
)
generated = outputs[0][inputs["input_ids"].shape[1]:]
content = provider._tokenizer.decode(generated, skip_special_tokens=True).strip()
print(f"\n=== GENERATED ({len(generated)} tokens) ===")
print(repr(content))
print()

# Test _extract_json_block
match = re.search(r"\{.*\}", content, flags=re.DOTALL)
if match:
    print("JSON match:", repr(match.group(0)))
    try:
        payload = json.loads(match.group(0))
        print("Parsed:", payload)
    except Exception as e:
        print("Parse error:", e)
else:
    print("No JSON block found!")
    m2 = re.search(r"-?\d+", content)
    print(f"Number extraction: {m2.group(0) if m2 else 'none'}")

print()
print("=== Now calling provider.predict() directly ===")
out = provider.predict(
    question="数字 2 一共有几位？",
    expected_answer="2",
    budget=100.0,
    mode=mode,
    stage=stage,
)
print(f"Final: answer={out.answer!r} conf={out.confidence}")
